"""text_analysis.py — 文本词云分析模块
自动识别开放题，jieba 中文分词，词云图 + 词频柱状图。
无系统中文字体时自动 fallback 到 wordcloud 内置字体（英文可正常显示，
若需中文词云请将 simhei.ttf 放入项目根目录）。
"""
import streamlit as st
import plotly.express as px
import pandas as pd
from collections import Counter
from io import BytesIO
import os


# ── 停用词（内置常用中文停用词）──
DEFAULT_STOPWORDS = set("""
的 了 是 在 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有
看 好 自己 这 那 来 用 些 而 将 与 地 对 过 后 如果 时 年 我们 他 她 它 们
从 但 所以 因为 如 但是 然后 还 吗 呢 啊 哦 哈 嗯 可以 这个 那个 什么 怎么
""".split())


def _try_jieba(text_list, extra_stopwords):
    """使用 jieba 分词，返回词频 Counter。"""
    import jieba
    jieba.setLogLevel(60)  # 静默
    stopwords = DEFAULT_STOPWORDS | set(extra_stopwords)
    words = []
    for text in text_list:
        for w in jieba.cut(str(text)):
            w = w.strip()
            if len(w) > 1 and w not in stopwords:
                words.append(w)
    return Counter(words)


def _build_wordcloud(word_freq, font_path, bg_color, width=800, height=400):
    """生成词云 PIL Image。"""
    from wordcloud import WordCloud
    wc = WordCloud(
        font_path=font_path if font_path and os.path.exists(font_path) else None,
        background_color=bg_color,
        width=width, height=height,
        max_words=150,
        colormap='tab10',
        collocations=False,
    )
    wc.generate_from_frequencies(word_freq)
    return wc.to_image()


def render(df, colors):
    """文本分析主渲染函数。"""
    questions = [q for q in df.columns if '序号' not in q]

    st.markdown('### 💬 文本词云分析')

    # ── 自动识别开放题 ──
    from analysis_engine import SurveyEngine
    open_qs = [q for q in questions if SurveyEngine.detect_question_type(df[q]) == '开放题']
    all_qs_choice = questions  # 允许用户手动选任意列

    hint = f'自动识别到 {len(open_qs)} 个开放题' if open_qs else '未自动识别到开放题，可手动选择任意列'
    st.caption(hint)

    sel_default = open_qs[0] if open_qs else questions[0]
    sel_q = st.selectbox('选择要分析的文本列', all_qs_choice,
                         index=all_qs_choice.index(sel_default), key='text_q')

    # ── 参数设置 ──
    cfg1, cfg2, cfg3 = st.columns(3)
    with cfg1:
        top_n = st.slider('展示 Top N 词', 5, 50, 20, key='text_topn')
    with cfg2:
        bg_color = st.color_picker('词云背景色', '#FFFFFF', key='text_bg')
    with cfg3:
        extra_sw = st.text_input('追加停用词（空格分隔）', '', key='text_sw')

    # 字体路径：优先项目根目录的 simhei.ttf
    font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'simhei.ttf')
    if not os.path.exists(font_path):
        font_path = None

    if st.button('▶ 生成词云分析', key='text_run', use_container_width=True):
        texts = df[sel_q].dropna().tolist()
        if len(texts) == 0:
            st.warning('该列无有效数据。')
            return

        extra_stopwords = extra_sw.split() if extra_sw.strip() else []

        with st.spinner('分词中…'):
            try:
                word_freq = _try_jieba(texts, extra_stopwords)
            except Exception:
                # jieba 失败时退化为简单分词
                stopwords = DEFAULT_STOPWORDS | set(extra_stopwords)
                all_words = []
                for t in texts:
                    for w in str(t).split():
                        w = w.strip('，。！？,.!? ')
                        if len(w) > 1 and w not in stopwords:
                            all_words.append(w)
                word_freq = Counter(all_words)

        if not word_freq:
            st.warning('分词后无有效词汇，请检查停用词设置。')
            return

        top_words = word_freq.most_common(top_n)
        freq_df = pd.DataFrame(top_words, columns=['词语', '频次'])

        # ── 左词云 右柱状图（左右布局，方便截图）──
        left, right = st.columns([1.2, 1], gap='large')

        with left:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown('##### ☁️ 词云图')
            try:
                wc_img = _build_wordcloud(dict(word_freq), font_path, bg_color)
                buf = BytesIO()
                wc_img.save(buf, format='PNG')
                st.image(buf.getvalue(), use_column_width=True)
                st.download_button(
                    '📥 下载词云图 PNG', data=buf.getvalue(),
                    file_name=f'词云_{sel_q[:6]}.png', mime='image/png',
                    use_container_width=True
                )
                if font_path is None:
                    st.caption('提示：未检测到 simhei.ttf，中文可能显示为方块。'
                               '将 simhei.ttf 放入项目根目录即可显示中文词云。')
            except Exception as e:
                st.error(f'词云生成失败：{e}')
            st.markdown('</div>', unsafe_allow_html=True)

        with right:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(f'##### 📊 Top {top_n} 高频词')
            fig = px.bar(
                freq_df.sort_values('频次'),
                x='频次', y='词语',
                orientation='h',
                text='频次',
                color_discrete_sequence=[colors[0]],
            )
            fig.update_traces(textposition='outside', textfont=dict(size=12, weight='bold'))
            fig.update_layout(
                height=max(350, top_n * 22),
                plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
                margin=dict(t=10, l=10, r=30, b=20),
                xaxis=dict(title='频次'),
                yaxis=dict(title='', autorange=True),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown('##### 📋 词频明细表')
            st.dataframe(freq_df, use_container_width=True, hide_index=True)
            csv_bytes = freq_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                '📥 导出词频 CSV', data=csv_bytes,
                file_name=f'词频_{sel_q[:6]}.csv',
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
