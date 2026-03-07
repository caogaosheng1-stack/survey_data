import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# --- 1. 页面配置：可爱风格设置 ---
st.set_page_config(page_title="屿寻摄影·数据分析中心", page_icon="🐱", layout="wide")

# 自定义 CSS：粉色主题、圆角和 Hello Kitty 氛围
st.markdown("""
    <style>
    .main {
        background-color: #FFF0F5; /* 薰衣草粉 */
    }
    h1 {
        color: #FF69B4; /* 热粉色 */
        font-family: 'Microsoft YaHei';
        text-align: center;
    }
    .stButton>button {
        background-color: #FFB6C1;
        color: white;
        border-radius: 20px;
        border: none;
    }
    /* 隐藏 Streamlit 默认页脚 */
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 交互界面：头部图片与欢迎语 ---
st.title("💖 屿寻摄影·问卷分享中心 💖")

# 这里的图片文件名请确保与你文件夹中的一致
col1, col2, col3 = st.columns(3)
with col1:
    # st.image("pic1.jpg", caption="风格展示 1", use_container_width=True)
    st.image("https://img.icons8.com/color/96/hello-kitty.png", width=100)  # 占位符图片
with col2:
    st.write("### Hello! 欢迎使用分析工具 ✨")
    st.write("在这里上传你的 Excel/CSV 文件，秒出可视化分析报告结果哦~")
with col3:
    st.image("https://img.icons8.com/color/96/hello-kitty.png", width=100)  # 占位符图片

# 展示你上传的那三张图片（你可以将路径换成你自己的图片名）
st.subheader("📸 我们的摄影作品展示")
img_cols = st.columns(3)
# 假设你已经把那三张图放在了同一个文件夹
# for i, img_path in enumerate(["4cc69fb5a039693e9db2333f87d9d0ab.jpg", "2faa8f262f76942e7e71b781a1c58eeb.jpg", "c7f800b3438c7c92baf9dd85b6856d5a.jpg"]):
#     img_cols[i].image(img_path, use_container_width=True)

---

# --- 3. 文件上传功能 ---
uploaded_file = st.file_uploader("👉 请点击下方按钮上传你的问卷数据 (Excel 或 CSV)", type=["xlsx", "csv"])

if uploaded_file is not None:
    # 读取数据
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("🎉 数据加载成功！准备开始分析...")

    # 获取所有问题列（排除序号等）
    questions = [col for col in df.columns if col != '序号']

    # 侧边栏选择问题进行分析
    st.sidebar.header("🎀 分析选项")
    selected_q = st.sidebar.selectbox("选择你想分析的问题：", questions)
    chart_type = st.sidebar.radio("选择图表类型：", ["柱状图", "饼图", "折线图"])

    # --- 4. 数据分析与可视化逻辑 (同你之前的代码) ---
    st.subheader(f"📊 分析结果：{selected_q}")

    # 处理逻辑（示例：简单频率统计）
    # 注意：这里的逻辑可以根据你之前的 survey_analysis_app.py 深度定制
    all_answers = []
    for item in df[selected_q].dropna():
        if isinstance(item, str) and "；" in item:  # 处理多选
            all_answers.extend([x.strip() for x in item.split("；")])
        else:
            all_answers.append(str(item).strip())

    counts = pd.Series(all_answers).value_counts()

    # 画图
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文显示
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = ['#FFB6C1', '#FFC0CB', '#FF69B4', '#DB7093', '#FF1493']  # 粉色系配色

    if chart_type == "柱状图":
        counts.plot(kind='bar', color=colors, ax=ax)
    elif chart_type == "饼图":
        counts.plot(kind='pie', autopct='%1.1f%%', colors=colors, ax=ax)
    else:
        counts.plot(kind='line', marker='o', color='#FF69B4', ax=ax)

    st.pyplot(fig)

    # 显示原始数据表
    with st.expander("查看原始频率统计数据"):
        st.write(counts)

else:
    st.info("☁️ 等待上传文件中...")