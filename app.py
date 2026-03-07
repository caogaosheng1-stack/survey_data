import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# --- 1. 深度定制：可爱风主题 CSS ---
st.set_page_config(page_title="屿寻摄影·分析中心", page_icon="🐾", layout="wide")

st.markdown("""
    <style>
    /* 整体背景与文字颜色 */
    .stApp {
        background-color: #FFF5F7;
    }
    .main h1 {
        color: #FF69B4 !important;
        font-family: 'Comic Sans MS', cursive, sans-serif;
        text-shadow: 2px 2px #FFD1DC;
    }
    /* 卡片式容器 */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 2px solid #FFB6C1;
        border-radius: 15px;
        padding: 10px;
    }
    /* 侧边栏美化 */
    section[data-testid="stSidebar"] {
        background-color: #FFECF1;
    }
    /* 自定义按钮 */
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        border: 2px solid #FF69B4;
        background-color: #FFB6C1;
        color: white;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #FF69B4;
        border-color: #FF1493;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心逻辑函数 (复刻你原代码的灵魂) ---
def process_survey_data(df, column):
    """处理多选题逻辑：拆分 '；' 并计算百分比"""
    valid_data = df[column].dropna()
    all_answers = []
    for item in valid_data:
        # 兼容你的 Excel 逻辑：如果是多选则拆分
        parts = [p.strip() for p in str(item).split('；') if p.strip()]
        all_answers.extend(parts)
    
    counts = Counter(all_answers)
    labels = list(counts.keys())
    values = list(counts.values())
    
    # 计算百分比（基于总样本数）
    total_samples = len(df)
    percents = [(v / total_samples) * 100 for v in values]
    
    return pd.DataFrame({"选项": labels, "频数": values, "占比(%)": percents}).sort_values("频数", ascending=False)

# --- 3. 侧边栏交互 ---
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

# --- 4. 主界面布局 ---
st.title("🐱 屿寻摄影·智能问卷分析系统")

if uploaded_file:
    # 数据读取
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    
    # 顶部关键指标展示 (Metrics)
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("总样本数", f"{len(df)} 份")
    col_m2.metric("有效问题数", f"{len(df.columns)-1} 个")
    col_m3.metric("状态", "✅ 分析就绪")

    # 使用 Tabs 优化交互体验
    tab1, tab2, tab3 = st.tabs(["📊 单题深度分析", "📋 原始数据", "💡 快速帮助"])

    with tab1:
        # 选择问题
        questions = [c for c in df.columns if c != '序号']
        selected_q = st.selectbox("请选择要分析的问题：", questions)
        
        chart_col, table_col = st.columns([2, 1])
        
        # 处理数据
        res_df = process_survey_data(df, selected_q)
        
        with chart_col:
            chart_type = st.segmented_control("图表类型", ["柱状图", "饼图", "折线图"], default="柱状图")
            
            plt.rcParams['font.sans-serif'] = ['SimHei']
            fig, ax = plt.subplots(figsize=(10, 6), facecolor='#FFF5F7')
            
            if chart_type == "柱状图":
                bars = ax.bar(res_df["选项"], res_df["频数"], color=palettes[palette_choice])
                ax.set_ylabel("选择次数")
            elif chart_type == "饼图":
                ax.pie(res_df["频数"], labels=res_df["选项"], autopct='%1.1f%%', colors=palettes[palette_choice], startangle=140)
            else:
                ax.plot(res_df["选项"], res_df["频数"], marker='o', color='#FF69B4', linewidth=2)
            
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig)
            
        with table_col:
            st.markdown("#### 数据详情")
            st.dataframe(res_df, use_container_width=True, hide_index=True)

    with tab2:
        st.write("您可以预览上传的完整数据：")
        st.dataframe(df)

else:
    # 默认展示的欢迎界面
    st.info("👋 欢迎！请在左侧上传您的问卷 Excel 文件开始分析。")
    # 这里可以放你刚才上传的那三张照片的展示代码
    # st.image(["pic1.jpg", "pic2.jpg", "pic3.jpg"], caption=["作品1", "作品2", "作品3"], width=200)
