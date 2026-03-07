import pandas as pd
import re
from collections import Counter

class SurveyEngine:
    @staticmethod
    def load_data(file):
        """加载 Excel 或 CSV 数据"""
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        return pd.read_excel(file)

    @staticmethod
    def process_column(df, column_name):
        """
        核心分析逻辑：
        1. 过滤空值
        2. 正则拆分多选题（支持中英文分号）
        3. 计算频数和基于有效样本的百分比
        """
        valid_series = df[column_name].dropna()
        total_samples = len(valid_series)
        
        if total_samples == 0:
            return None

        all_answers = []
        for val in valid_series:
            # 复刻原代码的正则拆分
            parts = [p.strip() for p in re.split('[;；]', str(val)) if p.strip()]
            all_answers.extend(parts)
        
        counts = Counter(all_answers)
        # 按频数降序排列
        sorted_data = counts.most_common()
        
        labels = [item[0] for item in sorted_data]
        values = [item[1] for item in sorted_data]
        # 百分比 = (选择人数 / 总回答人数) * 100
        percents = [(v / total_samples) * 100 for v in values]
        
        return {
            "labels": labels,
            "values": values,
            "percents": percents,
            "total": total_samples
        }
