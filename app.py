import streamlit as st
import plotly.express as px
import pandas as pd
import re
from analysis_engine import SurveyEngine

# --- 1. 全局配置与高级卡片模板 CSS ---
st.set_page_config(page_title="棍棍的数据分析日记", page_icon="📒", layout="wide")

st.markdown("""
    <style>
    /* 页面基础背景色（极浅的灰色，用来衬托纯白卡片） */
    .stApp { background-color: #F4F6F9; }
    
    /* 全局字体放大加粗 */
    html, body, [class*="st-"] {
        font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif !important;
        font-size: 17px !important; /* 字体调大 */
        font-weight: 600 !important; /* 全局半加粗 */
        color: #2C3E50;
    }
    
    /* 专属大标题美化 */
    h1 { 
        color: #FF69B4 !important; 
        text-align: center; 
        font-weight: 900 !important; 
        font-size: 2.8rem !important;
        text-shadow: 2px 2px 4px rgba(255,105,180,0.15);
        margin-bottom: 0.5rem !important;
    }
    h3, h4 { color: #34495E !important; font-weight: 800 !important; margin-top: 0 !important; }
    
    /* 极致紧凑的页面间距 */
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; max-width: 96% !important; }
    
    /* 高级悬浮卡片模板 (指标、图例、数据表) */
    div[data-testid="stMetric"], .legend-box, [data-testid="stDataFrame"] {
        background-color: #FFFFFF;
        border: 1px solid #EAECEF;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        padding: 15px;
    }
    
    /* 指标数字特大加粗 */
    div[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 900 !important; color: #FF69B4 !important;}
    
    /* 下拉框标签加粗加大 */
    label { font-size: 1.1rem !important; font-weight: 800 !important; color: #2C3E50 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 智能提取标号函数 ---
def get_short_label(text):
    text_str = str(text).strip()
    match = re.match(r'^([A-Za-z])[\.、\s]', text_str)
    if match: return match.group(1).upper()
    return text_str if len(text_str) <= 4 else text_str[:3] + ".."

# --- 2. 侧边栏控制台 ---
with st.sidebar:
    st.image("https://img.icons8.com/color/144/hello-kitty.png", width=120)
    st.markdown("### ⚙️ 日记控制台")
    uploaded_file = st.file_uploader("📂 上传问卷数据", type=["xlsx", "csv"])
    
    palettes = SurveyEngine.get_palettes()
    color_theme = st.selectbox("🎨 图表配色模板", list(palettes.keys()), index=1)
    current_colors = palettes[color_theme]

# --- 3. 页面主视图 ---
st.markdown("<h1>📒 棍棍的数据分析日记 📒</h1>", unsafe_allow_html=True)

if uploaded_file:
    try:
        df = SurveyEngine.load_data(uploaded_file)
        
        # 紧凑指标卡片
        c1, c2, c3 = st.columns(3)
        c1.metric("📌 总样本量", f"{len(df)} 份")
        c2.metric("🎯 题目数量", f"{len(df.columns) - 1} 项")
        c3.metric("✨ 分析状态", "数据已就绪")
        st.markdown("<br>", unsafe_allow_html=True)

        # --- 核心操作区 ---
        questions = [q for q in df.columns if "序号" not in q]
        selected_q = st.selectbox("👉 请选择要查看的日记维度：", questions)
        
        res_df, others_list = SurveyEngine.process_question(df, selected_q)

        if res_df is not None:
            res_df["简称"] = res_df["选项"].apply(get_short_label)
            legend_dict = dict(zip(res_df["简称"], res_df["选项"]))

            # 黄金比例布局
            col_chart, col_data = st.columns([1.6, 1], gap="medium")
            
            with col_chart:
                chart_type = st.radio("切换可视化", ["实心饼状图", "柱状图", "趋势折线图"], horizontal=True, label_visibility="collapsed")
                
                # --- 图表生成：纯白底色，字体加粗加大 ---
                if chart_type == "实心饼状图":
                    fig = px.pie(res_df, names="简称", values="频数", hover_data=["选项"], color_discrete_sequence=current_colors)
                    fig.update_traces(textposition='inside', textinfo='percent+label', 
                                      insidetextfont=dict(color='white', size=16, family='Arial Black', weight='bold'))
                
                elif chart_type == "柱状图":
                    fig = px.bar(res_df, x="简称", y="频数", text="占比(%)", hover_data=["选项"], color="简称", color_discrete_sequence=current_colors)
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside', 
                                      textfont=dict(size=16, color='#2C3E50', weight='bold'))
                    fig.update_layout(showlegend=False)
                
                else:
                    fig = px.line(res_df, x="简称", y="频数", markers=True, text="频数", hover_data=["选项"], color_discrete_sequence=[current_colors[2]])
                    fig.update_traces(line=dict(width=5), marker=dict(size=12), textfont=dict(size=16, weight='bold'), textposition="top center")

                # 图表背景纯白，极其紧凑
                fig.update_layout(
                    plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
                    margin=dict(t=20, l=10, r=10, b=10),
                    xaxis=dict(showgrid=True, gridcolor='#F0F2F6', title="", tickfont=dict(size=14, weight='bold')),
                    yaxis=dict(showgrid=True, gridcolor='#F0F2F6', title="频数", tickfont=dict(size=14, weight='bold'))
                )
                
                # 在白底卡片中渲染图表
                st.markdown('<div style="background-color: white; padding: 10px; border-radius: 12px; border: 1px solid #EAECEF; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # --- 底部图例卡片 ---
                st.markdown('<div class="legend-box">', unsafe_allow_html=True)
                st.markdown("#### 📌 选项对照说明")
                for short_k, full_v in legend_dict.items():
                    st.markdown(f"**{short_k}** — {full_v}")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_data:
                # --- 数据明细卡片 ---
                st.markdown("### 📋 频率明细表")
                st.dataframe(
                    res_df[["选项", "频数", "占比(%)"]].style.format({"占比(%)": "{:.2f}%"}),
                    use_container_width=True, hide_index=True
                )
                
                csv_data = res_df[["选项", "频数", "占比(%)"]].to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 导出今日日记 (CSV)", data=csv_data, file_name=f"棍棍日记_{selected_q[:5]}.csv", use_container_width=True)
                
                # “其他”选项加粗提示
                if others_list:
                    st.markdown('<div class="legend-box">', unsafe_allow_html=True)
                    st.markdown("#### 📝 【其他】填空原话提取：")
                    for text in set(others_list):
                        st.markdown(f"🔹 {text}")
                    st.markdown('</div>', unsafe_allow_html=True)
                elif "其他" in res_df["选项"].values:
                    st.warning("⚠️ 选择了“其他”但未填写内容")

    except Exception as e:
        st.error(f"❌ 读取日记时遇到问题: {e}")
else:
    st.info("💡 棍棍，请在左侧上传数据文件，开启今天的分析日记吧！")
