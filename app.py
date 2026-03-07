import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import re

# --- 1. 页面配置与可爱风 CSS ---
st.set_page_config(page_title="屿寻摄影·分析中心", page_icon="🐾", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    .main h1 { color: #FF69B4 !important; font-family: 'Microsoft YaHei', sans-serif; text-shadow: 2px 2px #FFD1DC; text-align: center; }
    div[data-testid="stMetric"] { background-color: #FFFFFF; border: 2px solid #FFB6C1; border-radius: 15px; padding: 10px; }
    section[data-testid="stSidebar"] { background-color: #FFECF1; }
    .stButton>button { width: 100%; border-radius: 20px; border: 2px solid #FF69B4; background-color: #FFB6C1; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心逻辑函数 ---
def process_survey_data(df, column):
    """处理多选题逻辑：兼容中英文分号"""
    valid_data = df[column].dropna()
    all_answers = []
    for item in valid_data:
        # 同时支持英文分号 ; 和中文分号 ；
        parts = [p.strip() for p in re.split('[;；]', str(item)) if p.strip()]
        all_answers.extend(parts)
    
    counts = Counter(all_answers)
    labels = list(counts.keys())
    values = list(counts.values())
    
    # 占比计算：基于有效填写人数
    total_valid = len(valid_data)
    percents = [(v / total_valid) * 100 for v in values] if total_valid > 0 else []
    
    res = pd.DataFrame({"选项": labels, "频数": values, "占比(%)": percents})
    return res.sort_values("频数", ascending=False)

# --- 3. 侧边栏 ---
with st.sidebar:
    st.markdown("## 🎀 控制面板")
    uploaded_file = st.file_uploader("第一步：上传数据", type=["xlsx", "csv"])
    
    palette_choice = st.selectbox("第二步：选择配色方案", ["甜美粉", "清新绿", "商务蓝", "马卡龙"])
    palettes = {
        "甜美粉": ['#FFB6C1', '#FFC0CB', '#FF69B4', '#DB7093', '#FF1493'],
        "清新绿": ['#98D8C8', '#4ECDC4', '#A0E7E5', '#B4F8C8', '#FBE7C6'],
        "商务蓝": ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c'],
        "马卡龙": ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#FFD9BA']
    }

# --- 4. 主界面 ---
st.title("🐱 屿寻摄影·智能问卷分析系统")

if uploaded_file:
    try:
        # 数据读取
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("总样本数", f"{len(df)} 份")
        col_m2.metric("字段数量", f"{len(df.columns)} 个")
        col_m3.metric("状态", "✅ 已就绪")

        tab1, tab2 = st.tabs(["📊 深度分析", "📋 原始数据"])

        with tab1:
            questions = [c for c in df.columns if c != '序号']
            selected_q = st.selectbox("请选择要分析的问题：", questions)
            
            # 使用更稳定的 radio 代替 segmented_control 以防版本兼容问题
            chart_type = st.radio("选择图表类型", ["柱状图", "饼图", "折线图"], horizontal=True)
            
            res_df = process_survey_data(df, selected_q)
            
            # 绘图环境设置
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif'] # 尽量兼容云端
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ax = plt.subplots(figsize=(10, 6), facecolor='#FFF5F7')
            
            if chart_type == "柱状图":
                bars = ax.bar(res_df["选项"], res_df["频数"], color=palettes[palette_choice])
                for bar in bars:
                    yval = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2, yval + 0.5, yval, ha='center', va='bottom')
            elif chart_type == "饼图":
                ax.pie(res_df["频数"], labels=res_df["选项"], autopct='%1.1f%%', colors=palettes[palette_choice])
            else:
                ax.plot(res_df["选项"], res_df["频数"], marker='o', color='#FF69B4', linewidth=2)

            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig)
            st.dataframe(res_df, use_container_width=True)

        with tab2:
            st.dataframe(df)
            
    except Exception as e:
        st.error(f"处理文件时出错啦：{e}")

else:
    st.info("👋 欢迎！请在左侧上传问卷 Excel 开始。")
    # 安全显示图片逻辑
    try:
        # 如果你以后想加图片，把图片上传后取消下面三行的注释即可
        # st.image(["pic1.jpg", "pic2.jpg"], width=300)
        pass
    except:
        pass
