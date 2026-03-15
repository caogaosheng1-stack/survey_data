import pandas as pd
import re
from collections import Counter
import numpy as np


class SurveyEngine:
    """
    核心分析引擎：统一版本，消除 app.py 与 analysis_engine.py 的重复定义。
    所有模块均从此处导入，不再各自实现。
    """

    # ------------------------------------------------------------------
    # 数据加载
    # ------------------------------------------------------------------
    @staticmethod
    def load_data(file):
        """加载数据，兼容 csv 和 excel"""
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        return pd.read_excel(file, engine='openpyxl')

    # ------------------------------------------------------------------
    # 配色方案
    # ------------------------------------------------------------------
    @staticmethod
    def get_palettes():
        return {
            '基础系 (Primary)':  ['#1890FF', '#2FC25B', '#FACC14', '#F04864', '#8543E0', '#13C2C2', '#3436C7', '#223273'],
            '马卡龙 (Pastel)':   ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#FFD9BA', '#D9BAFF', '#FFB3BA'],
            '商务蓝 (Business)': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2'],
            '温馨暖色 (Warm)':   ['#8B4513', '#CD5C5C', '#F08080', '#BC8F8F', '#DEB887', '#F5DEB3', '#FFE4B5'],
            '清凉冷色 (Cool)':   ['#4682B4', '#5F9EA0', '#66CDAA', '#7FFFD4', '#B0E0E6', '#87CEFA', '#B0C4DE'],
        }

    # ------------------------------------------------------------------
    # 单题处理（多选题拆分 + 频数统计）
    # ------------------------------------------------------------------
    @staticmethod
    def process_question(df, col_name):
        """
        核心算法：多选题拆分、频数统计及「其他」选项详情提取。
        返回: (res_df, others_detail_list)
        """
        valid_data = df[col_name].dropna()
        total_samples = len(valid_data)
        if total_samples == 0:
            return None, []

        all_answers = []
        others_detail = []

        for item in valid_data:
            parts = [p.strip() for p in re.split(r'[;；]', str(item)) if p.strip()]
            for p in parts:
                if '其他' in p or '其它' in p:
                    # 统一归为「其他」一类，不再细分「其他（xxx）」变体
                    all_answers.append('其他')
                    # 提取括号内容作为补充说明展示，不作为独立选项计数
                    match = re.search(r'[（\(](.*?)[）\)]', p)
                    if match:
                        content = match.group(1).strip()
                        if content:
                            others_detail.append(content)
                    else:
                        content = p.replace('其他', '').replace('其它', '').strip('()（） :：')
                        if content:
                            others_detail.append(content)
                else:
                    # 普通选项：去掉尾部括号补充说明，只保留主体内容
                    clean_p = re.sub(r'[（\(][^）\)]*[）\)]$', '', p).strip()
                    all_answers.append(clean_p if clean_p else p)

        counts = Counter(all_answers)
        res_df = pd.DataFrame({
            '选项':   list(counts.keys()),
            '频数':   list(counts.values()),
            '占比(%)': [(v / total_samples) * 100 for v in counts.values()],
        })
        return res_df, others_detail

    # ------------------------------------------------------------------
    # 题目类型自动识别
    # ------------------------------------------------------------------
    @staticmethod
    def detect_question_type(series):
        """
        返回 '多选题' / '开放题' / '单选题'
        """
        valid = series.dropna()
        if len(valid) == 0:
            return '未知'
        has_semicolon = valid.astype(str).str.contains(r'[;；]').any()
        if has_semicolon:
            return '多选题'
        unique_ratio = valid.nunique() / len(valid)
        if unique_ratio > 0.6:
            return '开放题'
        return '单选题'

    # ------------------------------------------------------------------
    # 交叉分析：将多选列 explode 为单值
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_other(val):
        """
        将任何包含「其他」/「其它」的单元格值统一替换为「其他」。
        用于 explode 之后的列清洗，避免「F. 其他」「G. 其他」等变体在交叉表中变成多列。
        """
        s = str(val).strip()
        if '其他' in s or '其它' in s:
            return '其他'
        # 去掉选项字母前缀（如 "A. "、"B、"）只保留文字主体，保持与单题分析一致
        s = re.sub(r'^[A-Za-z][.、\s]+', '', s).strip()
        return s if s else val

    @staticmethod
    def explode_column(df, col_name):
        """
        将含分号的多选列拆分展开，返回新 DataFrame（行数会增加）。
        若为单选列，原样返回。
        展开后自动将所有「其他」变体统一为「其他」，避免交叉表出现多个「其他」列。
        """
        import re as _re
        series = df[col_name].dropna()
        if series.astype(str).str.contains(r'[;；]').any():
            expanded = df.copy()
            expanded[col_name] = expanded[col_name].astype(str).str.split(r'[;；]')
            expanded = expanded.explode(col_name)
            expanded[col_name] = expanded[col_name].str.strip()
            expanded = expanded[expanded[col_name] != '']
        else:
            expanded = df.copy()
        # 统一「其他」变体 + 去掉字母前缀
        expanded[col_name] = expanded[col_name].apply(SurveyEngine._normalize_other)
        return expanded

    # ------------------------------------------------------------------
    # 交叉表计算
    # ------------------------------------------------------------------
    @staticmethod
    def build_crosstab(df, row_col, col_col, filter_col=None, filter_val=None):
        """
        计算交叉频数表。
        支持可选的第三维度过滤（filter_col / filter_val）。
        自动处理多选题 explode。
        返回: (freq_df, row_pct_df, col_pct_df)
        """
        dff = df.copy()
        # 第三维度过滤
        if filter_col and filter_val:
            dff = SurveyEngine.explode_column(dff, filter_col)
            dff = dff[dff[filter_col].astype(str).str.strip() == str(filter_val)]

        # 多选题展开
        dff = SurveyEngine.explode_column(dff, row_col)
        dff = SurveyEngine.explode_column(dff, col_col)

        dff = dff[[row_col, col_col]].dropna()
        dff[row_col] = dff[row_col].astype(str).str.strip()
        dff[col_col] = dff[col_col].astype(str).str.strip()

        # 过滤掉字符串 'nan' / 'None' / 空字符串（explode 后的残留脏数据）
        _bad = {'nan', 'none', 'null', '', 'na'}
        dff = dff[~dff[row_col].str.lower().isin(_bad)]
        dff = dff[~dff[col_col].str.lower().isin(_bad)]

        if dff.empty:
            empty = pd.DataFrame()
            return empty, empty, empty

        freq = pd.crosstab(dff[row_col], dff[col_col])
        # 交叉表本身的 NaN 用 0 填充（某组合无数据时显示 0 而非 nan）
        freq = freq.fillna(0).astype(int)

        # ── 行索引智能排序：纯数字按数值升序，文字按原始出现顺序 ──
        def _sort_index(idx):
            def _key(v):
                s = str(v).strip()
                # 提取开头的数字部分（如 "18-25岁" 提取 18，"A.男" 提取不到则用文字排序）
                m = re.match(r'^([\d.]+)', s)
                return (0, float(m.group(1))) if m else (1, s)
            return sorted(idx, key=_key)

        sorted_rows = _sort_index(freq.index.tolist())
        sorted_cols = _sort_index(freq.columns.tolist())
        freq = freq.loc[sorted_rows, sorted_cols]

        row_pct = freq.div(freq.sum(axis=1), axis=0) * 100
        col_pct = freq.div(freq.sum(axis=0), axis=1) * 100
        # 百分比中可能因除以 0 产生 NaN，同样填 0
        row_pct = row_pct.fillna(0)
        col_pct = col_pct.fillna(0)

        return freq, row_pct.round(2), col_pct.round(2)

    # ------------------------------------------------------------------
    # 统计检验
    # ------------------------------------------------------------------
    @staticmethod
    def chi2_test(freq_df):
        """
        对交叉频数表执行卡方独立性检验。
        返回: dict {chi2, p, dof, cramers_v, strength, conclusion}
        """
        from scipy.stats import chi2_contingency
        chi2, p, dof, _ = chi2_contingency(freq_df.values)
        n = freq_df.values.sum()
        r, c = freq_df.shape
        cramers_v = np.sqrt(chi2 / (n * (min(r, c) - 1))) if min(r, c) > 1 else 0

        if cramers_v < 0.1:
            strength = '弱'
        elif cramers_v < 0.3:
            strength = '中'
        else:
            strength = '强'

        if p < 0.001:
            p_str = '< 0.001'
        else:
            p_str = f'{p:.3f}'

        conclusion = (
            f'p = {p_str} < 0.05，两变量存在显著关联（{strength}关联，Cramer\'s V = {cramers_v:.3f}）'
            if p < 0.05
            else f'p = {p_str} ≥ 0.05，两变量无显著关联'
        )
        return {
            'chi2': round(chi2, 4),
            'p': round(p, 4),
            'dof': dof,
            'cramers_v': round(cramers_v, 4),
            'strength': strength,
            'conclusion': conclusion,
        }

    @staticmethod
    def correlation_matrix(df, cols):
        """
        计算指定列的 Pearson 相关系数矩阵。
        会尝试将列转换为数值型，无法转换的列自动跳过。
        """
        numeric_df = df[cols].apply(pd.to_numeric, errors='coerce')
        valid_cols = numeric_df.dropna(axis=1, how='all').columns.tolist()
        if len(valid_cols) < 2:
            return None
        return numeric_df[valid_cols].corr()

    @staticmethod
    def group_mean(df, group_col, value_col):
        """
        按 group_col 分组，计算 value_col 的均值和标准差。
        value_col 会尝试转换为数值型。
        返回 DataFrame: {group, mean, std, count}
        """
        tmp = df[[group_col, value_col]].copy()
        tmp[value_col] = pd.to_numeric(tmp[value_col], errors='coerce')
        tmp = tmp.dropna()
        result = tmp.groupby(group_col)[value_col].agg(['mean', 'std', 'count']).reset_index()
        result.columns = ['分组', '均值', '标准差', '样本量']
        result['均值'] = result['均值'].round(3)
        result['标准差'] = result['标准差'].round(3)
        return result
