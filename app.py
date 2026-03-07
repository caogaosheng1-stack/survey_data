import streamlit as st
import plotly.express as px
import pandas as pd
import re
from analysis_engine import SurveyEngine

# --- 1. 全局配置与极简纯白 CSS ---
st.set_page_config(page_title="屿寻摄影·智能问卷系统", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    h1 { color: #333333 !important; text-align: center; font-family: 'Microsoft YaHei', sans-serif; font-weight: bold; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    [data-testid="stDataFrame"] { background-color: #FFFFFF; }
    /* 图例说明框美化 */
    .legend-box { background-color: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 8px; padding: 15px; margin-top: 10px;}
    </style>
    """, unsafe_allow_html=True)

# --- 智能提取标号函数 ---
def get_short_label(text):
    """自动提取 A/B/C/D 标号，如果没有则截断过长文字"""
    text_str = str(text).strip()
    # 匹配 "A."、"B、"、"C " 等开头的格式
    match = re.match(r'^([A-Za-z])[\.、\s]', text_str)
    if match:
        return match.group(1).upper() # 返回 A, B, C
    # 如果没有标号，且超过4个字，打省略号
    return text_str if len(text_str) <= 4 else text_str[:3] + ".."

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
            # ✅ 新增：为图表生成“简称”和“图例字典”
            res_df["简称"] = res_df["选项"].apply(get_short_label)
            legend_dict = dict(zip(res_df["简称"], res_df["选项"]))

            col_chart, col_data = st.columns([1.5, 1], gap="large")
            
            with col_chart:
                chart_type = st.radio("切换视图", ["实心饼状图", "柱状图", "趋势折线图"], horizontal=True, label_visibility="collapsed")
                
                # --- 图表生成：使用“简称”作图，鼠标悬停显示“选项”全称 ---
                if chart_type == "实心饼状图":
                    fig = px.pie(res_df, names="简称", values="频数", 
                                 hover_data=["选项"], # 鼠标放上去显示全称
                                 color_discrete_sequence=current_colors)
                    fig.update_traces(textposition='inside', textinfo='percent+label', 
                                      insidetextfont=dict(color='white', size=14, family='Arial Black'))
                
                elif chart_type == "柱状图":
                    fig = px.bar(res_df, x="简称", y="频数", text="占比(%)", 
                                 hover_data=["选项"], # 鼠标放上去显示全称
                                 color="简称", color_discrete_sequence=current_colors)
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside', 
                                      textfont=dict(size=14, color='#333'))
                    fig.update_layout(showlegend=False)
                
                else:
                    fig = px.line(res_df, x="简称", y="频数", markers=True, text="频数",
                                  hover_data=["选项"],
                                  color_discrete_sequence=[current_colors[2]])
                    fig.update_traces(line=dict(width=4), marker=dict(size=10), textposition="top center")

                # 图表 UI：纯白背景
                fig.update_layout(
                    plot_bgcolor='#FFFFFF', 
                    paper_bgcolor='#FFFFFF',
                    margin=dict(t=30, l=10, r=10, b=10),
                    xaxis=dict(showgrid=True, gridcolor='#E5E5E5', title=""),
                    yaxis=dict(showgrid=True, gridcolor='#E5E5E5', title="频数")
                )
                st.plotly_chart(fig, use_container_width=True)

                # ✅ 新增：在图表正下方渲染纯白底色的“图例说明”
                st.markdown('<div class="legend-box">', unsafe_allow_html=True)
                st.markdown("##### 📌 图例对照说明")
                for short_k, full_v in legend_dict.items():
                    # 判断如果选项全称已经包含了 A.，图例就直接展示全称即可，看起来更自然
                    st.caption(f"**{short_k}** —  {full_v}")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_data:
                st.markdown("#### 📋 数据统计明细")
                # 数据表格中依然展示【完整名称】，保证数据准确性
                st.dataframe(
                    res_df[["选项", "频数", "占比(%)"]].style.format({"占比(%)": "{:.2f}%"}),
                    use_container_width=True, 
                    hide_index=True
                )
                
                csv_data = res_df[["选项", "频数", "占比(%)"]].to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 导出明细 (CSV)", data=csv_data, file_name=f"分析_{selected_q[:5]}.csv", use_container_width=True)
                
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
