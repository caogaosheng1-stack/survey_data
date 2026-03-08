import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import re
from collections import Counter

# ==========================================
# 🧠 第一部分：后台数据分析引擎 (稳定核心不变)
# ==========================================
class SurveyEngine:
    @staticmethod
    def load_data(file):
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        return pd.read_excel(file, engine='openpyxl')

    @staticmethod
    def get_palettes():
        return {
            '基础系 (Primary)': ['#1890FF', '#2FC25B', '#FACC14', '#F04864', '#8543E0', '#13C2C2', '#3436C7', '#223273'],
            '马卡龙 (Pastel)': ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#FFD9BA', '#D9BAFF', '#FFB3BA'],
            '商务蓝 (Business)': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2'],
            '温馨暖色 (Warm)': ['#8B4513', '#CD5C5C', '#F08080', '#BC8F8F', '#DEB887', '#F5DEB3', '#FFE4B5'],
            '清凉冷色 (Cool)': ['#4682B4', '#5F9EA0', '#66CDAA', '#7FFFD4', '#B0E0E6', '#87CEFA', '#B0C4DE']
        }

    @staticmethod
    def process_question(df, col_name):
        valid_data = df[col_name].dropna()
        total_samples = len(valid_data)
        if total_samples == 0: return None, []

        all_answers = []
        others_detail = []

        for item in valid_data:
            parts = [p.strip() for p in re.split(r'[;；]', str(item)) if p.strip()]
            for p in parts:
                if "其他" in p or "其它" in p:
                    all_answers.append("其他")
                    match = re.search(r'[（\(](.*?)[）\)]', p)
                    if match:
                        content = match.group(1).strip()
                        if content: others_detail.append(content)
                    else:
                        content = p.replace("其他", "").replace("其它", "").strip("()（） ")
                        if content: others_detail.append(content)
                else:
                    all_answers.append(p)

        counts = Counter(all_answers)
        res_df = pd.DataFrame({
            "选项": list(counts.keys()),
            "频数": list(counts.values()),
            "占比(%)": [(v / total_samples) * 100 for v in counts.values()]
        })
        return res_df, others_detail

# ==========================================
# 🎨 第二部分：UI 界面与 1:1 图表复刻
# ==========================================
st.set_page_config(page_title="屿寻摄影·智能问卷系统", page_icon="📒", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F4F6F9; }
    html, body, [class*="st-"] {
        font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif !important;
        font-size: 15px !important; font-weight: 600 !important; color: #2C3E50;
    }
    h1 { color: #FF69B4 !important; text-align: center; font-weight: 900 !important; font-size: 2.6rem !important; margin-bottom: 0.5rem !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; max-width: 98% !important; } 
    
    .report-card {
        background-color: #FFFFFF; border: 1px solid #DCDFE6; 
        border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
        padding: 20px; height: 100%;
    }
    [data-testid="stDataFrame"] { border: 1px solid #EBEEF5; border-radius: 8px; overflow: hidden; }
    div[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 900 !important; color: #FF69B4 !important;}
    
    .legend-text { font-size: 14px !important; color: #444; margin-bottom: 8px; line-height: 1.5;}
    .legend-text b { color: #2C3E50; font-weight: 800 !important; font-size: 14.5px;}
    </style>
    """, unsafe_allow_html=True)

def extract_existing_letter(text):
    match = re.match(r'^([A-Za-z])[\.、\s]', str(text).strip())
    return match.group(1).upper() if match else None

def clean_full_text(text):
    return re.sub(r'^([A-Za-z])[\.、\s]+', '', str(text).strip())

# --- 侧边栏 ---
with st.sidebar:
    st.image("https://img.icons8.com/color/144/hello-kitty.png", width=120)
    st.markdown("### ⚙️ 控制中心")
    uploaded_file = st.file_uploader("📂 上传问卷数据", type=["xlsx", "csv"])
    
    palettes = SurveyEngine.get_palettes()
    color_theme = st.selectbox("🎨 图表配色主题", list(palettes.keys()), index=0)
    current_colors = palettes[color_theme]

# --- 页面主视图 ---
st.markdown("<h1>📒 屿寻摄影·智能问卷分析台 📒</h1>", unsafe_allow_html=True)

if uploaded_file:
    try:
        df = SurveyEngine.load_data(uploaded_file)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📌 总样本量", f"{len(df)} 份")
        c2.metric("🎯 题目数量", f"{len(df.columns) - 1} 项")
        c3.metric("✨ 分析状态", "数据已就绪")
        st.markdown("<br>", unsafe_allow_html=True)

        questions = [q for q in df.columns if "序号" not in q]
        selected_q = st.selectbox("👉 请选择要查看的题目：", questions)
        
        res_df, others_list = SurveyEngine.process_question(df, selected_q)

        if res_df is not None:
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
            
            res_df = res_df.sort_values(by="简称", ascending=True).reset_index(drop=True)
            legend_dict = dict(zip(res_df["简称"], res_df["纯净解释"]))

            # ==========================================
            # 🚀 左表右图：双栏核心结构
            # ==========================================
            col_left_table, col_right_visuals = st.columns([1, 1.8], gap="large")
            
            with col_left_table:
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.markdown("### 📋 频率明细表")
                st.dataframe(
                    res_df[["简称", "选项", "频数", "占比(%)"]].style.format({"占比(%)": "{:.2f}%"}),
                    use_container_width=True, hide_index=True, height=480
                )
                csv_data = res_df[["选项", "频数", "占比(%)"]].to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 导出明细 (CSV)", data=csv_data, file_name=f"数据导出_{selected_q[:5]}.csv", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col_right_visuals:
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                
                # 【完全对标 PDF：5种图表水平切换】
                chart_type = st.radio("视图", ["饼状图", "圆环图", "柱状图", "条形图", "折线图"], horizontal=True, label_visibility="collapsed")
                st.markdown("<hr style='margin: 5px 0 15px 0; border: 0; border-top: 1px solid #EEE;'>", unsafe_allow_html=True)
                
                inner_chart, inner_text = st.columns([1.5, 1], gap="medium")
                
                with inner_chart:
                    # 强行预设最高值为 Y 轴顶点，确保 75 刻度完美展现
                    max_pct = res_df['占比(%)'].max()
                    y_range = [0, max(80, max_pct * 1.15)]
                    c_main = current_colors[0] # 主题单色（用于柱状、条形、折线）
                    
                    # 生成图表时，强制使用格式化文本，确保多选题在饼图中依然显示绝对普及率
                    formatted_text = res_df["占比(%)"].apply(lambda x: f"{x:.2f}%")

                    if chart_type in ["饼状图", "圆环图"]:
                        hole_size = 0.45 if chart_type == "圆环图" else 0
                        fig = px.pie(res_df, names="纯净解释", values="频数", hole=hole_size, color_discrete_sequence=current_colors)
                        # 核心复刻：引线在外部，强行显示普及率数值
                        fig.update_traces(
                            text=formatted_text, textinfo='text', textposition='outside', 
                            marker=dict(line=dict(color='#FFFFFF', width=1.5)),
                            insidetextorientation='horizontal'
                        )
                        # 核心复刻：图例放置在底部
                        fig.update_layout(
                            legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5, font=dict(size=12)),
                            showlegend=True
                        )

                    elif chart_type == "柱状图":
                        fig = px.bar(res_df, x="纯净解释", y="占比(%)", text=formatted_text)
                        fig.update_traces(marker_color=c_main, textposition='outside', textfont=dict(size=13, weight='bold'), width=0.45)
                        fig.update_layout(
                            yaxis=dict(tickvals=[0, 25, 50, 75], range=y_range, title=""),
                            xaxis=dict(tickangle=45, title=""), showlegend=False
                        )

                    elif chart_type == "条形图":
                        fig = px.bar(res_df, x="占比(%)", y="纯净解释", text=formatted_text, orientation='h')
                        fig.update_traces(marker_color=c_main, textposition='outside', textfont=dict(size=13, weight='bold'), width=0.45)
                        fig.update_layout(
                            xaxis=dict(tickvals=[0, 25, 50, 75], range=y_range, title=""),
                            yaxis=dict(autorange="reversed", title=""), showlegend=False
                        )

                    elif chart_type == "折线图":
                        fig = px.line(res_df, x="纯净解释", y="占比(%)", text=formatted_text, markers=True)
                        fig.update_traces(
                            line=dict(color=c_main, width=3), 
                            marker=dict(size=10, color=c_main, line=dict(color='white', width=1.5)),
                            textposition='top center', textfont=dict(size=13, weight='bold')
                        )
                        fig.update_layout(
                            yaxis=dict(tickvals=[0, 25, 50, 75], range=y_range, title=""),
                            xaxis=dict(tickangle=45, title=""), showlegend=False
                        )

                    # 统一的底层 UI 清洗（白底、防重叠）
                    fig.update_layout(
                        height=430, plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
                        margin=dict(t=20, l=10, r=10, b=40 if chart_type in ["饼状图", "圆环图"] else 10),
                        xaxis=dict(showgrid=True, gridcolor='#F0F2F6'), 
                        yaxis=dict(showgrid=True, gridcolor='#F0F2F6')
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with inner_text:
                    st.markdown("<h4 style='color:#34495E; margin-bottom:15px;'>📌 选项说明</h4>", unsafe_allow_html=True)
                    for short_k, pure_v in legend_dict.items():
                        st.markdown(f"<div class='legend-text'><b>{short_k}</b> — {pure_v}</div>", unsafe_allow_html=True)
                    
                    if others_list:
                        st.markdown("<hr style='margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
                        st.markdown("<h5 style='color:#E67E22; margin-top:10px;'>📝 【其他】补充明细：</h5>", unsafe_allow_html=True)
                        for text in set(others_list):
                            st.markdown(f"<div class='legend-text' style='color:#7F8C8D;'>🔹 {text}</div>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ 读取数据时遇到问题: {e}")
else:
    st.info("💡 请在左侧上传问卷数据文件，启动智能分析引擎！")
