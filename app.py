import streamlit as st
import plotly.express as px
import pandas as pd
import re
from analysis_engine import SurveyEngine

# --- 1. 全局配置与高级卡片模板 CSS ---
st.set_page_config(page_title="棍棍的数据分析日记", page_icon="📒", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F4F6F9; }
    html, body, [class*="st-"] {
        font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif !important;
        font-size: 16px !important; 
        font-weight: 600 !important; 
        color: #2C3E50;
    }
    h1 { color: #FF69B4 !important; text-align: center; font-weight: 900 !important; font-size: 2.8rem !important; text-shadow: 2px 2px 4px rgba(255,105,180,0.15); margin-bottom: 0.5rem !important; }
    h3, h4 { color: #34495E !important; font-weight: 800 !important; margin-top: 0 !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; max-width: 98% !important; } 
    
    /* 卡片化样式 */
    div[data-testid="stMetric"], .legend-box-bottom, [data-testid="stDataFrame"] {
        background-color: #FFFFFF; border: 1px solid #EAECEF; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04); padding: 15px; 
    }
    div[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 900 !important; color: #FF69B4 !important;}
    
    /* 底部图例文字样式：适中大小，不过分抢占图表风头 */
    .legend-text { font-size: 14.5px !important; color: #555; font-weight: 500 !important; line-height: 1.6;}
    .legend-text b { color: #2C3E50; font-weight: 800 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 智能文本处理函数 ---
def extract_existing_letter(text):
    """提取已有的 A, B, C 等标号"""
    match = re.match(r'^([A-Za-z])[\.、\s]', str(text).strip())
    return match.group(1).upper() if match else None

def clean_full_text(text):
    """去掉选项全称前面的 'A. ', 'B、' 等前缀"""
    return re.sub(r'^([A-Za-z])[\.、\s]+', '', str(text).strip())

# --- 2. 侧边栏 ---
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
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📌 总样本量", f"{len(df)} 份")
        c2.metric("🎯 题目数量", f"{len(df.columns) - 1} 项")
        c3.metric("✨ 分析状态", "数据已就绪")
        st.markdown("<br>", unsafe_allow_html=True)

        questions = [q for q in df.columns if "序号" not in q]
        selected_q = st.selectbox("👉 请选择要查看的日记维度：", questions)
        
        res_df, others_list = SurveyEngine.process_question(df, selected_q)

        if res_df is not None:
            # === 核心逻辑：智能分配顺延标号 ===
            res_df["现有标号"] = res_df["选项"].apply(extract_existing_letter)
            existing_letters = res_df["现有标号"].dropna().tolist()
            
            # 找到当前用到的最大字母（如 'F'），准备顺延
            next_char_code = ord(max(existing_letters)) + 1 if existing_letters else ord('A')
            
            def assign_short_label(row):
                nonlocal next_char_code
                if pd.notna(row["现有标号"]):
                    return row["现有标号"]
                else:
                    new_letter = chr(next_char_code)
                    next_char_code += 1 # 顺延给下一个没有字母的选项
                    return new_letter

            res_df["简称"] = res_df.apply(assign_short_label, axis=1)
            res_df["纯净解释"] = res_df["选项"].apply(clean_full_text)
            
            # 按 ABCD 强制重新排序
            res_df = res_df.sort_values(by="简称", ascending=True).reset_index(drop=True)
            legend_dict = dict(zip(res_df["简称"], res_df["纯净解释"]))

            # --- 全局布局：左侧图+文 (占大头)，右侧表格 ---
            col_left_main, col_right_table = st.columns([2.5, 1], gap="large")
            
            with col_left_main:
                chart_type = st.radio("切换可视化", ["横向柱状图", "竖向柱状图", "实心饼状图"], horizontal=True, label_visibility="collapsed")
                
                # ==== 1. 上半部分：核心图表 ====
                if chart_type == "横向柱状图":
                    fig = px.bar(res_df, x="频数", y="简称", text="占比(%)", orientation='h', color="简称", color_discrete_sequence=current_colors)
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside', textfont=dict(size=15, weight='bold'))
                    fig.update_layout(yaxis=dict(autorange="reversed"), bargap=0.4, showlegend=False) # bargap=0.4 让柱子变细
                
                elif chart_type == "竖向柱状图":
                    fig = px.bar(res_df, x="简称", y="频数", text="占比(%)", color="简称", color_discrete_sequence=current_colors)
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside', textfont=dict(size=15, weight='bold'))
                    fig.update_layout(bargap=0.4, showlegend=False) 
                
                else: 
                    fig = px.pie(res_df, names="简称", values="频数", color_discrete_sequence=current_colors)
                    fig.update_traces(textposition='inside', textinfo='percent+label', insidetextfont=dict(color='white', size=16, family='Arial Black', weight='bold'))

                fig.update_layout(
                    height=450, # 增加图表高度，突出“图是主题”
                    plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
                    margin=dict(t=20, l=10, r=20, b=10),
                    xaxis=dict(showgrid=True, gridcolor='#F0F2F6', title=""),
                    yaxis=dict(showgrid=True, gridcolor='#F0F2F6', title="")
                )
                
                st.markdown('<div style="background-color: white; padding: 15px; border-radius: 12px; border: 1px solid #EAECEF; box-shadow: 0 4px 12px rgba(0,0,0,0.04); margin-bottom: 15px;">', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # ==== 2. 下半部分：文字解释图例 ====
                st.markdown('<div class="legend-box-bottom">', unsafe_allow_html=True)
                st.markdown("#### 📌 选项对照说明")
                # 使用 Flexbox 自动排版，省空间又整齐
                legend_html = "<div style='display: flex; flex-wrap: wrap; gap: 10px;'>"
                for short_k, pure_v in legend_dict.items():
                    legend_html += f"<div style='flex: 1 1 45%; min-width: 250px;' class='legend-text'><b>{short_k}</b> — {pure_v}</div>"
                legend_html += "</div>"
                st.markdown(legend_html, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col_right_table:
                # --- 右侧：数据明细表格 ---
                st.markdown("### 📋 频率明细表")
                st.dataframe(
                    res_df[["简称", "选项", "频数", "占比(%)"]].style.format({"占比(%)": "{:.2f}%"}),
                    use_container_width=True, hide_index=True, height=520 # 调高表格以对齐左侧图文
                )
                
                csv_data = res_df[["选项", "频数", "占比(%)"]].to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 导出今日数据 (CSV)", data=csv_data, file_name=f"棍棍日记_{selected_q[:5]}.csv", use_container_width=True)
                
                if others_list:
                    st.markdown('<div class="legend-box-bottom" style="margin-top: 15px;">', unsafe_allow_html=True)
                    st.markdown("#### 📝 【其他】原话提取：")
                    for text in set(others_list):
                        st.markdown(f"<div class='legend-text'>🔹 {text}</div>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ 读取日记时遇到问题: {e}")
else:
    st.info("💡 棍棍，请在左侧上传数据文件，开启今天的分析日记吧！")
