import streamlit as st
import pandas as pd
import plotly.express as px
import re
from collections import Counter

# --- 1. 页面配置 ---
st.set_page_config(page_title="屿寻摄影·智能分析中心", page_icon="🐾", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; }
    h1 { color: #FF69B4 !important; text-align: center; }
    .stMetric { background-color: white; border: 2px solid #FFB6C1; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心逻辑：复刻原代码“其他”逻辑 ---
def process_data_with_others(df, column):
    valid_series = df[column].dropna()
    total_samples = len(valid_series)
    
    all_answers = []
    others_detail = [] # 用于存储“其他”的具体内容
    
    for item in valid_series:
        item_str = str(item)
        # 拆分选项
        parts = [p.strip() for p in re.split('[;；]', item_str) if p.strip()]
        
        for p in parts:
            # 原代码逻辑：如果选项包含“其他”，提取括号里的内容
            if "其他" in p:
                all_answers.append("其他")
                # 提取“其他（xxx）”中的 xxx
                match = re.search(r'[（\(](.*?)[）\)]', p)
                if match:
                    others_detail.append(match.group(1))
                else:
                    # 如果没有括号，就把整段话作为详情（去掉“其他”字样）
                    detail = p.replace("其他", "").strip("()（） ")
                    if detail: others_detail.append(detail)
            else:
                all_answers.append(p)
                
    counts = Counter(all_answers)
    res_df = pd.DataFrame({
        "选项": list(counts.keys()),
        "频数": list(counts.values())
    })
    res_df["占比(%)"] = (res_df["频数"] / total_samples * 100).round(2)
    
    return res_df.sort_values("频数", ascending=False), others_detail

# --- 3. 侧边栏交互 ---
with st.sidebar:
    st.header("🎀 配置中心")
    uploaded_file = st.file_uploader("上传问卷数据", type=["xlsx", "csv"])
    
    # 配色方案（Plotly 专用颜色序列）
    palette_map = {
        "甜美粉": ["#FFB6C1", "#FF69B4", "#FF1493", "#DB7093", "#FFC0CB"],
        "清新绿": ["#98D8C8", "#4ECDC4", "#A0E7E5", "#B4F8C8", "#FBE7C6"],
        "商务蓝": ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"],
        "马卡龙": ["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#FFD9BA"]
    }
    color_choice = st.selectbox("更换图表配色", list(palette_map.keys()))

# --- 4. 主界面布局 ---
st.title("🐱 屿寻摄影·智能问卷分析系统")

if uploaded_file:
    # 读数据
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    
    # 指标栏
    c1, c2, c3 = st.columns(3)
    c1.metric("总样本", f"{len(df)} 份")
    c2.metric("当前状态", "✅ 运行中")
    
    questions = [c for c in df.columns if "序号" not in c]
    selected_q = st.selectbox("选择要分析的问题", questions)
    
    # 处理数据
    res_df, others_list = process_data_with_others(df, selected_q)
    
    tab1, tab2 = st.tabs(["📊 可视化分析", "📋 数据详情"])
    
    with tab1:
        chart_type = st.radio("选择图表", ["柱状图", "饼图"], horizontal=True)
        
        if chart_type == "柱状图":
            fig = px.bar(res_df, x="选项", y="频数", text="占比(%)",
                         color_discrete_sequence=palette_map[color_choice])
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        else:
            fig = px.pie(res_df, names="选项", values="频数",
                         color_discrete_sequence=palette_map[color_choice])
        
        # 解决中文显示的关键：Plotly 默认支持多语言
        fig.update_layout(title=f"问题：{selected_q}", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        # --- 重点：备注“其他”详情 ---
        if others_list:
            with st.expander("📝 查看“其他”选项的具体内容"):
                st.write("朋友们填写的“其他”包括：")
                for i, detail in enumerate(set(others_list)): # set去重
                    st.write(f"{i+1}. {detail}")
        elif "其他" in res_df["选项"].values:
            st.info("该问题的“其他”选项暂无具体文字描述。")

    with tab2:
        st.dataframe(res_df, use_container_width=True)
else:
    st.info("👋 欢迎！请在侧边栏上传文件，我将为你进行魔法般的分析~")
