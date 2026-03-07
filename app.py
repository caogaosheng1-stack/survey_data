import streamlit as st
import plotly.express as px
import pandas as pd
from analysis_engine import SurveyEngine

# --- 1. 全局配置与极简专业 CSS ---
st.set_page_config(page_title="屿寻摄影·智能问卷系统", page_icon="🎀", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF0F5; }
    h1 { color: #FF69B4 !important; text-align: center; font-family: 'Microsoft YaHei', sans-serif; font-weight: 900; }
    /* 数据表格美化 */
    [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(255,105,180,0.1); }
    /* 顶部卡片 */
    div[data-testid="stMetric"] { background-color: rgba(255, 255, 255, 0.9); border-left: 5px solid #FFB6C1; border-radius: 8px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 侧边栏：配置与上传 ---
with st.sidebar:
    st.image("https://img.icons8.com/color/144/hello-kitty.png", use_container_width=True)
    st.markdown("## ⚙️ 系统控制台")
    uploaded_file = st.file_uploader("📂 上传问卷数据", type=["xlsx", "csv"])
    
    palettes = SurveyEngine.get_palettes()
    color_theme = st.selectbox("🎨 图表配色主题", list(palettes.keys()), index=1)
    current_colors = palettes[color_theme]

# --- 3. 顶部横幅 ---
st.title("🎀 屿寻摄影·全景数据看板 🎀")

if uploaded_file:
    try:
        df = SurveyEngine.load_data(uploaded_file)
        
        # 顶部指标卡
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("总回收样本量", f"{len(df)} 份")
        c2.metric("有效题目数", f"{len(df.columns) - 1} 题")
        c3.metric("当前配色", color_theme.split(' ')[0])
        c4.metric("引擎状态", "🟢 正常")
        
        st.markdown("---")

        # --- 🎯 核心交互区：选择题目 ---
        questions = [q for q in df.columns if "序号" not in q]
        selected_q = st.selectbox("👇 请选择需要分析的题目：", questions)
        
        # 获取后台数据
        res_df, others_list = SurveyEngine.process_question(df, selected_q)

        if res_df is not None:
            # --- 📊 数据展示模块 (经典左右布局：左图右表) ---
            st.markdown("### 📊 交叉分析看板")
            col_chart, col_data = st.columns([1.5, 1]) # 比例：图占 60%，表占 40%
            
            with col_chart:
                # 顶部小控制条
                chart_type = st.segmented_control("切换视图", ["极简柱状图", "环形饼图", "趋势折线图"], default="极简柱状图")
                
                if chart_type == "极简柱状图":
                    fig = px.bar(res_df, x="选项", y="频数", text="占比(%)", color="选项", color_discrete_sequence=current_colors)
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig.update_layout(showlegend=False)
                elif chart_type == "环形饼图":
                    fig = px.pie(res_df, names="选项", values="频数", hole=0.4, color_discrete_sequence=current_colors)
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                else:
                    fig = px.line(res_df, x="选项", y="频数", markers=True, color_discrete_sequence=[current_colors[2]])
                    fig.update_traces(line=dict(width=4), marker=dict(size=12, color=current_colors[0]))

                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, l=10, r=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

            with col_data:
                st.markdown("#### 📋 频率明细表")
                # 展示高亮的数据表
                st.dataframe(
                    res_df.style.format({"占比(%)": "{:.2f}%"}).background_gradient(subset=['频数'], cmap='RdPu'),
                    use_container_width=True, 
                    hide_index=True,
                    height=300 # 固定高度让排版更整齐
                )
                
                # 一键导出按钮紧跟表格下方
                csv_data = res_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 导出表格数据 (CSV)", data=csv_data, file_name=f"分析结果.csv", mime="text/csv", use_container_width=True)
                
                # “其他”选项内容直接以卡片形式展示在表格下方
                if others_list:
                    with st.expander("📝 查看手填【其他】明细", expanded=True):
                        for i, text in enumerate(set(others_list)):
                            st.caption(f"· {text}")
                elif "其他" in res_df["选项"].values:
                    st.info("⚠️ 有用户选择“其他”但未填具体内容")

        else:
            st.warning("⚠️ 该题目暂无有效作答数据。")

        # --- 📸 底部作品展示区 ---
        st.markdown("---")
        with st.expander("🌸 屿寻客片展示墙 (点击展开)"):
            img_col1, img_col2, img_col3 = st.columns(3)
            try:
                img_col1.image("4cc69fb5a039693e9db2333f87d9d0ab.jpg", use_container_width=True)
                img_col2.image("2faa8f262f76942e7e71b781a1c58eeb.jpg", use_container_width=True)
                img_col3.image("c7f800b3438c7c92baf9dd85b6856d5a.jpg", use_container_width=True)
            except:
                st.caption("照片未加载（请确保照片与 app.py 在同一目录下）")

    except Exception as e:
        st.error(f"❌ 运行遇到障碍: {e}")

else:
    st.info("👋 请在左侧上传问卷数据以启动大屏。")
