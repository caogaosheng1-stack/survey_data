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
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; max-width: 96% !important; } 
    
    /* 高级白底卡片，带有边框和阴影 */
    .card-box, div[data-testid="stMetric"] {
        background-color: #FFFFFF; 
        border: 1px solid #DCDFE6; /* 明显的边框颜色 */
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
        padding: 20px; 
    }
    
    /* 强制给表格区域加上边框感 */
    [data-testid="stDataFrame"] { border: 1px solid #EBEEF5; border-radius: 8px; overflow: hidden; }
    
    div[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 900 !important; color: #FF69B4 !important;}
    .legend-text { font-size: 15px !important; color: #444; font-weight: 500 !important; margin-bottom: 8px;}
    .legend-text b { color: #2C3E50; font-weight: 800 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 智能文本处理函数 ---
def extract_existing_letter(text):
    match = re.match(r'^([A-Za-z])[\.、\s]', str(text).strip())
    return match.group(1).upper() if match else None

def clean_full_text(text):
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
            # === 安全顺延标号逻辑 ===
            res_df["现有标号"] = res_df["选项"].apply(extract_existing_letter)
            existing_letters = res_df["现有标号"].dropna().tolist()
            next_char_code = ord(max(existing_letters)) + 1 if existing_letters else ord('A')
            
            final_labels = []
            for val in res_df["现有标号"]:
                if pd.notna(val):
                    final_labels.append(val)
                else:
                    final_labels.append(chr(next_char_code))
                    next_char_code += 1 
                    
            res_df["简称"] = final_labels
            res_df["纯净解释"] = res_df["选项"].apply(clean_full_text)
            
            # 强制按 ABCD 正常排序
            res_df = res_df.sort_values(by="简称", ascending=True).reset_index(drop=True)
            legend_dict = dict(zip(res_df["简称"], res_df["纯净解释"]))

            # ==========================================
            # 🚀 全新布局：左边表格，右边图表+文字+其他
            # ==========================================
            col_left_table, col_right_visuals = st.columns([1, 1.4], gap="large")
            
            # ---------------- 左侧：数据表格 ----------------
            with col_left_table:
                st.markdown('<div class="card-box" style="height: 100%;">', unsafe_allow_html=True)
                st.markdown("### 📋 频率明细表")
                
                # 表格展示（包含简称和纯净文本）
                st.dataframe(
                    res_df[["简称", "选项", "频数", "占比(%)"]].style.format({"占比(%)": "{:.2f}%"}),
                    use_container_width=True, hide_index=True, height=450
                )
                
                # 导出按钮
                csv_data = res_df[["选项", "频数", "占比(%)"]].to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 导出表格 (CSV)", data=csv_data, file_name=f"棍棍日记_{selected_q[:5]}.csv", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # ---------------- 右侧：瀑布流视觉区 ----------------
            with col_right_visuals:
                st.markdown('<div class="card-box">', unsafe_allow_html=True)
                
                # 【1. 顶部：图表切换与饼图】
                chart_type = st.radio("视图切换", ["实心饼状图", "横向柱状图"], horizontal=True, label_visibility="collapsed")
                
                if chart_type == "实心饼状图":
                    fig = px.pie(res_df, names="简称", values="频数", color_discrete_sequence=current_colors)
                    fig.update_traces(textposition='inside', textinfo='percent+label', insidetextfont=dict(color='white', size=16, family='Arial Black', weight='bold'))
                else:
                    fig = px.bar(res_df, x="频数", y="简称", text="占比(%)", orientation='h', color="简称", color_discrete_sequence=current_colors)
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside', textfont=dict(size=15, weight='bold'))
                    fig.update_layout(yaxis=dict(autorange="reversed"), bargap=0.4, showlegend=False)
                
                fig.update_layout(
                    height=380, plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
                    margin=dict(t=10, l=10, r=20, b=10),
                    xaxis=dict(showgrid=True, gridcolor='#F0F2F6', title=""), yaxis=dict(showgrid=True, gridcolor='#F0F2F6', title="")
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---") # 分割线
                
                # 【2. 中部：选项文字解释】
                st.markdown("#### 📌 选项说明")
                # 使用两列并排展示，节省空间
                col_leg1, col_leg2 = st.columns(2)
                items = list(legend_dict.items())
                for i, (short_k, pure_v) in enumerate(items):
                    if i % 2 == 0:
                        col_leg1.markdown(f"<div class='legend-text'><b>{short_k}</b> — {pure_v}</div>", unsafe_allow_html=True)
                    else:
                        col_leg2.markdown(f"<div class='legend-text'><b>{short_k}</b> — {pure_v}</div>", unsafe_allow_html=True)
                
                # 【3. 底部：“其他”原话提取】
                if others_list:
                    st.markdown("---") # 分割线
                    st.markdown("#### 📝 【其他】补充明细")
                    for text in set(others_list):
                        st.markdown(f"<div class='legend-text' style='color:#E67E22;'>🔹 {text}</div>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ 读取日记时遇到问题: {e}")
else:
    st.info("💡 棍棍，请在左侧上传数据文件，开启今天的分析日记吧！")
