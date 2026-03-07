import streamlit as st
import plotly.express as px
import pandas as pd
from analysis_engine import SurveyEngine

# --- 1. 全局配置与极简纯白 CSS ---
st.set_page_config(page_title="屿寻摄影·智能问卷系统", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    /* 整体背景变淡，凸显核心数据区的纯白 */
    .stApp { background-color: #F8F9FA; }
    h1 { color: #333333 !important; text-align: center; font-family: 'Microsoft YaHei', sans-serif; font-weight: bold; }
    /* 隐藏顶部白边，更加紧凑 */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    /* 数据表格纯白底色 */
    [data-testid="stDataFrame"] { background-color: #FFFFFF; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 侧边栏 ---
with st.sidebar:
    st.image("https://img.icons8.com/color/144/hello-kitty.png", width=100)
    st.markdown("### ⚙️ 数据控制台")
    uploaded_file = st.file_uploader("📂 上传问卷数据", type=["xlsx", "csv"])
    
    palettes = SurveyEngine.get_palettes()
    color_theme = st.selectbox("🎨 图表配色主题", list(palettes.keys()), index=1)
    current_colors = palettes[color_theme]

st.title("📊 屿寻摄影·核心数据看板")

if uploaded_file:
    try:
        df = SurveyEngine.load_data(uploaded_file)
        
        # 紧凑型指标
        c1, c2, c3 = st.columns(3)
        c1.metric("总样本量", f"{len(df)} 份")
        c2.metric("有效分析维度", f"{len(df.columns) - 1} 项")
        c3.metric("当前状态", "🟢 数据已就绪")
        st.markdown("---")

        # --- 🎯 核心展示模块 ---
        questions = [q for q in df.columns if "序号" not in q]
        selected_q = st.selectbox("👇 请选择分析维度：", questions)
        
        res_df, others_list = SurveyEngine.process_question(df, selected_q)

        if res_df is not None:
            # 采用 6:4 的黄金分割比例
            col_chart, col_data = st.columns([1.5, 1], gap="large")
            
            with col_chart:
                chart_type = st.radio("切换视图", ["实心饼状图", "柱状图", "趋势折线图"], horizontal=True, label_visibility="collapsed")
                
                # --- 图表生成：纯白背景，数据直接写在图上 ---
                if chart_type == "实心饼状图":
                    # 取消 hole 参数，变为实心饼图
                    fig = px.pie(res_df, names="选项", values="频数", 
                                 color_discrete_sequence=current_colors)
                    # 数据写在图上：同时显示百分比和具体选项名，字体加粗
                    fig.update_traces(textposition='inside', textinfo='percent+label', 
                                      insidetextfont=dict(color='white', size=14, family='Arial Black'))
                
                elif chart_type == "柱状图":
                    fig = px.bar(res_df, x="选项", y="频数", text="占比(%)", 
                                 color="选项", color_discrete_sequence=current_colors)
                    # 数据写在柱子外侧上方
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside', 
                                      textfont=dict(size=14, color='#333'))
                    fig.update_layout(showlegend=False)
                
                else:
                    fig = px.line(res_df, x="选项", y="频数", markers=True, text="频数",
                                  color_discrete_sequence=[current_colors[2]])
                    fig.update_traces(line=dict(width=4), marker=dict(size=10), textposition="top center")

                # 图表 UI 紧凑化核心配置：纯白背景 (#FFFFFF)，极小边距
                fig.update_layout(
                    plot_bgcolor='#FFFFFF', 
                    paper_bgcolor='#FFFFFF',
                    margin=dict(t=30, l=10, r=10, b=10), # 极小边距，让图表撑满空间
                    xaxis=dict(showgrid=True, gridcolor='#E5E5E5', title=""),
                    yaxis=dict(showgrid=True, gridcolor='#E5E5E5', title="频数")
                )
                
                # 在 Streamlit 中渲染图表卡片
                st.plotly_chart(fig, use_container_width=True)

            with col_data:
                st.markdown("#### 📋 数据统计明细")
                # 紧凑型纯白数据表
                st.dataframe(
                    res_df.style.format({"占比(%)": "{:.2f}%"}),
                    use_container_width=True, 
                    hide_index=True
                )
                
                # 紧凑下载按钮
                csv_data = res_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 导出明细 (CSV)", data=csv_data, file_name=f"分析_{selected_q[:5]}.csv", use_container_width=True)
                
                # 如果有“其他”，紧凑展示
                if others_list:
                    st.markdown("**📝 “其他”填空明细：**")
                    for text in set(others_list):
                        st.caption(f"· {text}")
                elif "其他" in res_df["选项"].values:
                    st.caption("⚠️ 选择了“其他”但未填具体内容")

    except Exception as e:
        st.error(f"❌ 数据处理遇到问题: {e}")
else:
    st.info("💡 请在左侧上传问卷数据以生成可视化看板。")
