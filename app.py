import streamlit as st
from analysis_engine import SurveyEngine
import modules.overview as overview
import modules.single_analysis as single_analysis
import modules.cross_analysis as cross_analysis
import modules.stat_analysis as stat_analysis
import modules.text_analysis as text_analysis
import modules.export_report as export_report

# ══════════════════════════════════════════════
# 页面配置（保持原有不变）
# ══════════════════════════════════════════════
st.set_page_config(
    page_title='屿寻摄影·智能问卷系统',
    page_icon='📒',
    layout='wide'
)

st.markdown("""
    <style>
    .stApp { background-color: #F4F6F9; }
    html, body, [class*="st-"] {
        font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif !important;
        font-size: 15px !important; font-weight: 600 !important; color: #2C3E50;
    }
    h1 { color: #FF69B4 !important; text-align: center; font-weight: 900 !important;
         font-size: 2.6rem !important; margin-bottom: 0.5rem !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important;
                       max-width: 98% !important; }
    .report-card {
        background-color: #FFFFFF; border: 1px solid #DCDFE6;
        border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 20px; height: 100%;
    }
    [data-testid="stDataFrame"] { border: 1px solid #EBEEF5; border-radius: 8px; overflow: hidden; }
    div[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 900 !important;
                                       color: #FF69B4 !important; }
    .legend-text { font-size: 14px !important; color: #444; margin-bottom: 8px; line-height: 1.5; }
    .legend-text b { color: #2C3E50; font-weight: 800 !important; font-size: 14.5px; }
    /* Tab 美化 */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0 !important;
        font-weight: 700 !important;
        padding: 8px 18px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 侧边栏（完全保持原有结构不变）
# ══════════════════════════════════════════════
with st.sidebar:
    st.image('https://img.icons8.com/color/144/hello-kitty.png', width=120)
    st.markdown('### ⚙️ 控制中心')
    uploaded_file = st.file_uploader('📂 上传问卷数据', type=['xlsx', 'csv'])

    palettes = SurveyEngine.get_palettes()
    color_theme = st.selectbox('🎨 图表配色主题', list(palettes.keys()), index=0)
    current_colors = palettes[color_theme]

# ══════════════════════════════════════════════
# 页面标题
# ══════════════════════════════════════════════
st.markdown('<h1>📒 屿寻摄影·智能问卷分析台 📒</h1>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 数据加载 & session_state 共享
# ══════════════════════════════════════════════
if uploaded_file:
    try:
        if 'df' not in st.session_state or st.session_state.get('file_name') != uploaded_file.name:
            st.session_state['df'] = SurveyEngine.load_data(uploaded_file)
            st.session_state['file_name'] = uploaded_file.name
        df = st.session_state['df']
    except Exception as e:
        st.error(f'❌ 读取数据时遇到问题: {e}')
        st.stop()

    # ══════════════════════════════════════════
    # Tab 导航（6 个功能页）
    # ══════════════════════════════════════════
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        '📊 数据概览',
        '🔍 单题分析',
        '🔀 交叉分析',
        '📈 统计检验',
        '💬 文本分析',
        '📥 导出报告',
    ])

    with tab1:
        overview.render(df, current_colors)

    with tab2:
        single_analysis.render(df, current_colors)

    with tab3:
        cross_analysis.render(df, current_colors)

    with tab4:
        stat_analysis.render(df, current_colors)

    with tab5:
        text_analysis.render(df, current_colors)

    with tab6:
        export_report.render(df, current_colors)

else:
    st.info('💡 请在左侧上传问卷数据文件，启动智能分析引擎！')
