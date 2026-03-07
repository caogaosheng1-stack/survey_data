import pandas as pd
import re
from collections import Counter

class SurveyEngine:
    """
    核心分析引擎：完全复刻 survey_analysis_app.py 的底层逻辑
    """
    @staticmethod
    def load_data(file):
        """加载数据，兼容 csv 和 excel"""
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        # 必须指定 openpyxl，防止云端报错
        return pd.read_excel(file, engine='openpyxl') 

    @staticmethod
    def get_palettes():
        """完美复刻你原代码中的 5 种专业配色方案（Hex 色值一字不差）"""
        return {
            '基础系 (Primary)': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F67280', '#C06C84', '#6C5B7B'],
            '马卡龙 (Pastel)': ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#FFD9BA', '#D9BAFF', '#FFB3BA'],
            '商务蓝 (Business)': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2'],
            '温馨暖色 (Warm)': ['#8B4513', '#CD5C5C', '#F08080', '#BC8F8F', '#DEB887', '#F5DEB3', '#FFE4B5'],
            '清凉冷色 (Cool)': ['#4682B4', '#5F9EA0', '#66CDAA', '#7FFFD4', '#B0E0E6', '#87CEFA', '#B0C4DE']
        }

    @staticmethod
    def process_question(df, col_name):
        """
        核心算法：复刻多选题拆分、频数统计及“其他”选项详情提取
        """
        valid_data = df[col_name].dropna()
        total_samples = len(valid_data) # 百分比分母：有效回答总数

        if total_samples == 0:
            return None, []

        all_answers = []
        others_detail = []

        for item in valid_data:
            item_str = str(item)
            # 1. 完美复刻：支持中英文分号拆分多选
            parts = [p.strip() for p in re.split(r'[;；]', item_str) if p.strip()]

            for p in parts:
                # 2. 完美复刻：“其他”选项的正则化提取逻辑
                if "其他" in p or "其它" in p:
                    all_answers.append("其他")
                    # 提取括号里的具体内容：匹配中文括号（）或英文括号()
                    match = re.search(r'[（\(](.*?)[）\)]', p)
                    if match:
                        content = match.group(1).strip()
                        if content:
                            others_detail.append(content)
                    else:
                        # 如果没有括号，剔除“其他”二字，保留剩下的文字作为备注
                        content = p.replace("其他", "").replace("其它", "").strip("()（） ")
                        if content:
                            others_detail.append(content)
                else:
                    all_answers.append(p)

        # 3. 频数统计
        counts = Counter(all_answers)
        labels = list(counts.keys())
        values = list(counts.values())

        # 4. 占比计算 (基于该题的有效总人数)
        percents = [(v / total_samples) * 100 for v in values]

        # 返回处理好的 DataFrame 和 提取出的“其他”内容列表
        res_df = pd.DataFrame({
            "选项": labels,
            "频数": values,
            "占比(%)": percents
        }).sort_values("频数", ascending=False)

        return res_df, others_detail
