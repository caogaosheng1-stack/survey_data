import streamlit as st
import plotly.express as px
import pandas as pd
from analysis_engine import SurveyEngine

# --- 1. 全局配置与可爱风 CSS ---
st.set_page_config(page_title="屿寻摄影·智能问卷系统", page_icon="🎀", layout="wide")

st.markdown("""
    <style>
    /* 页面整体背景 */
    .stApp { background-color: #FFF0F5; }
    /* 标题美化 */
    h1 { color: #FF69B4 !important; text-align: center; font-family: 'Microsoft YaHei', sans-serif; font-weight: 900; letter-spacing: 2px; }
    h2, h3 { color: #FF1493 !important; font-family: 'Microsoft YaHei', sans-serif; }
    /* 顶部指标卡片 */
    div[data-testid="stMetric"] { 
        background-color: rgba(255, 255, 255, 0.8); 
        border-left: 5px solid #FFB6C1; 
        border-radius: 10px; 
        padding: 15px; 
        box-shadow: 0 4px 6px rgba(255, 105, 180, 0.1);
    }
    /* 侧边栏 */
    section[data-testid="stSidebar"] { background-color: #FFECF1; border-right: 2px dashed #FFB6C1; }
    /* Tab 标签页美化 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: white; border-radius: 10px 10px 0 0; 
        padding: 10px 20px; font-weight: bold; color: #FF69B4;
    }
    .stTabs [aria-selected="true"] { background-color: #FFB6C1; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 侧边栏：全局控制台 ---
with st.sidebar:
    st.image("https://img.icons8.com/color/144/hello-kitty.png", use_container_width=True)
    st.markdown("## ⚙️ 控制中心")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("📂 第一步：上传问卷数据", type=["xlsx", "csv"], help="支持包含多选题的 Excel 或 CSV 文件")
    
    palettes = SurveyEngine.get_palettes()
    color_theme = st.selectbox("🎨 第二步：选择视觉风格", list(palettes.keys()), index=1) # 默认选马卡龙色
    current_colors = palettes[color_theme]
    
    st.markdown("---")
    st.markdown("### 💡 系统信息")
    st.info("当前引擎版本：v2.0 (完美还原多选拆分与正则提取)")

# --- 3. 顶部横幅 ---
st.title("🎀 屿寻摄影·全景数据分析台 🎀")

if uploaded_file:
    try:
        # --- 模块 A：数据引擎加载 ---
        df = SurveyEngine.load_data(uploaded_file)
        
        # 顶部核心指标 (KPI)
        st.markdown("### 📈 问卷全局概览")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("总回收样本量", f"{len(df)} 份", "有效数据")
        c2.metric("问卷题目总数", f"{len(df.columns) - 1} 题")
        c3.metric("当前配色主题", color_theme.split(' ')[0])
        c4.metric("后台引擎状态", "🟢 满载运行中")
        
        st.markdown("<br>", unsafe_allow_html=True)

        # --- 功能模块划分：使用 Tabs 构建多级界面 ---
        tab_viz, tab_data, tab_gallery, tab_advance = st.tabs([
            "📊 单题可视化剖析", 
            "📋 报表生成与导出", 
            "📸 屿寻作品展示区", 
            "🧩 进阶功能探索"
        ])
        
        # ==========================================
        # 模块 1：核心可视化区 (图表展示)
        # ==========================================
        with tab_viz:
            st.markdown("#### 🎯 请选择需要深入分析的维度")
            questions = [q for q in df.columns if "序号" not in q]
            selected_q = st.selectbox("⬇️ 下拉选择问卷题目：", questions, label_visibility="collapsed")
            
            # 调用后台引擎
            res_df, others_list = SurveyEngine.process_question(df, selected_q)
            
            if res_df is not None:
                viz_col1, viz_col2 = st.columns([3, 1])
                
                with viz_col2:
                    st.markdown("#### 图表配置")
                    chart_type = st.radio("呈现方式", ["极简柱状图", "环形饼图", "趋势折线图"])
                    st.markdown("#### 核心结论")
                    top_choice = res_df.iloc[0]["选项"]
                    top_pct = res_df.iloc[0]["占比(%)"]
                    st.success(f"**最高频选项：**\n\n【{top_choice}】\n\n占据了 **{top_pct:.1f}%** 的比例。")

                with viz_col1:
                    # Plotly 交互图表
                    if chart_type == "极简柱状图":
                        fig = px.bar(res_df, x="选项", y="频数", text="占比(%)", color="选项",
                                     color_discrete_sequence=current_colors)
                        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                        fig.update_layout(showlegend=False)
                    elif chart_type == "环形饼图":
                        fig = px.pie(res_df, names="选项", values="频数", hole=0.4,
                                     color_discrete_sequence=current_colors)
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                    else:
                        fig = px.line(res_df, x="选项", y="频数", markers=True, 
                                      color_discrete_sequence=[current_colors[2]])
                        fig.update_traces(line=dict(width=4), marker=dict(size=12, color=current_colors[0]))

                    fig.update_layout(title=dict(text=f"问题：{selected_q}", font=dict(size=16)), 
                                      plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                      margin=dict(t=50, l=20, r=20, b=20))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ 该题目暂无有效作答数据。")

        # ==========================================
        # 模块 2：数据明细与导出
        # ==========================================
        with tab_data:
            st.markdown("#### 🗃️ 频率统计明细表")
            if res_df is not None:
                # 展示美化后的表格
                st.dataframe(res_df.style.format({"占比(%)": "{:.2f}%"}), 
                             use_container_width=True, hide_index=True)
                
                # 一键下载功能
                csv_data = res_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 导出当前分析结果 (CSV)",
                    data=csv_data,
                    file_name=f"分析结果_{selected_q[:10]}.csv",
                    mime="text/csv"
                )
                
                # 展示“其他”文本详情
                if others_list:
                    st.markdown("---")
                    st.markdown("#### 📝 用户手填“其他”备注汇总")
                    for i, text in enumerate(set(others_list)):
                        st.caption(f"{i+1}. {text}")

        # ==========================================
        # 模块 3：摄影作品画廊
        # ==========================================
        with tab_gallery:
            st.markdown("#### 🌸 屿寻摄影·当季客片精选")
            st.write("将美好的瞬间定格，让数据与艺术在这里相遇。")
            img_col1, img_col2, img_col3 = st.columns(3)
            
            # 这里的图片文件名对应你之前上传的文件
            try:
                img_col1.image("4cc69fb5a039693e9db2333f87d9d0ab.jpg", caption="屿寻客片 - 风格A", use_container_width=True)
                img_col2.image("2faa8f262f76942e7e71b781a1c58eeb.jpg", caption="屿寻客片 - 风格B", use_container_width=True)
                img_col3.image("c7f800b3438c7c92baf9dd85b6856d5a.jpg", caption="屿寻客片 - 风格C", use_container_width=True)
            except Exception:
                st.info("📷 提示：请确保照片文件已上传至同一目录下，即可在此处点亮作品墙。")

        # ==========================================
        # 模块 4：进阶探索 (预留模块)
        # ==========================================
        with tab_advance:
            st.markdown("#### 🔭 交叉分析与洞察 (敬请期待)")
            st.info("此模块为未来预留。后续可在此处接入：\n\n1. **交叉分析**：例如『不同预算的人群，对风格的偏好差异』。\n2. **AI 智能解读**：一键生成全篇问卷的数据洞察报告。")
            st.image("https://img.icons8.com/clouds/200/hello-kitty.png")

    except Exception as e:
        st.error(f"❌ 运行遇到一点小障碍: {e}")

else:
    # 欢迎引导界面
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col_w1, col_w2, col_w3 = st.columns([1, 2, 1])
    with col_w2:
        st.info("👋 欢迎来到屿寻摄影专属数据大屏！请在左侧面板上传您的 `Excel` 或 `CSV` 问卷数据文件，即可唤醒所有分析模块。")
