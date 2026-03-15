"""single_analysis.py — 单题分析模块
完整迁移原 app.py 的单题分析逻辑，保持「左表右图」布局不变，新增雷达图、颜色微调、PNG 导出。
"""
import streamlit as st
import pandas as pd
import re
from analysis_engine import SurveyEngine
from modules.chart_builder import build_single_chart


def extract_existing_letter(text):
    match = re.match(r'^([A-Za-z])[\.、\s]', str(text).strip())
    return match.group(1).upper() if match else None


def clean_full_text(text):
    return re.sub(r'^([A-Za-z])[\.、\s]+', '', str(text).strip())


def render(df, colors):
    """单题分析主渲染函数，由 app.py 的 Tab 调用。"""
    questions = [q for q in df.columns if '序号' not in q]
    selected_q = st.selectbox('请选择要查看的题目：', questions, key='single_q')

    res_df, others_list = SurveyEngine.process_question(df, selected_q)

    if res_df is None:
        st.warning('该题目暂无有效数据。')
        return

    # ── 字母标号处理（完整保留原逻辑）──
    res_df['现有标号'] = res_df['选项'].apply(extract_existing_letter)
    existing_letters = res_df['现有标号'].dropna().tolist()
    next_char_code = ord(max(existing_letters)) + 1 if existing_letters else ord('A')

    final_labels = []
    for val in res_df['现有标号']:
        if pd.notna(val):
            final_labels.append(val)
        else:
            final_labels.append(chr(next_char_code))
            next_char_code += 1
    res_df['简称'] = final_labels
    res_df['纯净解释'] = res_df['选项'].apply(clean_full_text)
    res_df = res_df.sort_values(by='简称', ascending=True).reset_index(drop=True)
    legend_dict = dict(zip(res_df['简称'], res_df['纯净解释']))

    # ── 左表 右图：双栏核心结构（保持原布局不变）──
    col_left_table, col_right_visuals = st.columns([1, 1.8], gap='large')

    with col_left_table:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown('### 📋 频率明细表')
        st.dataframe(
            res_df[['简称', '选项', '频数', '占比(%)']].style.format({'占比(%)': '{:.2f}%'}),
            use_container_width=True, hide_index=True, height=480
        )
        csv_data = res_df[['选项', '频数', '占比(%)']].to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            '导出明细 (CSV)', data=csv_data,
            file_name=f'数据导出_{selected_q[:5]}.csv', use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right_visuals:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)

        chart_type = st.radio(
            '视图', ['饼状图', '圆环图', '柱状图', '条形图', '折线图', '雷达图'],
            horizontal=True, label_visibility='collapsed', key='single_chart_type'
        )
        st.markdown("<hr style='margin:5px 0 15px 0;border:0;border-top:1px solid #EEE;'>",
                    unsafe_allow_html=True)

        # ── 颜色微调：每行最多 4 个，label 显示「简称: 前6字」避免重叠 ──
        custom_colors = []
        with st.expander('颜色微调（可选）', expanded=False):
            n_opts = len(res_df)
            n_cols = min(n_opts, 4)  # 每行最多 4 列，防止 label 文字重叠
            for row_start in range(0, n_opts, n_cols):
                chunk = res_df.iloc[row_start:row_start + n_cols]
                picker_cols = st.columns(n_cols)
                for j, (idx, opt_row) in enumerate(chunk.iterrows()):
                    default = colors[idx % len(colors)]
                    short_label = f"{opt_row['简称']}: {opt_row['纯净解释'][:5]}"
                    picked = picker_cols[j].color_picker(
                        short_label, default, key=f'cp_{idx}'
                    )
                    custom_colors.append(picked)
        active_colors = custom_colors if custom_colors else colors

        # ── 图表标题 ──
        chart_title = st.text_input('图表标题（导出时显示）', value=selected_q[:30], key='single_title')

        inner_chart, inner_text = st.columns([1.5, 1], gap='medium')

        with inner_chart:
            fig = build_single_chart(res_df, chart_type, active_colors, title=chart_title)
            st.plotly_chart(fig, use_container_width=True)

            # PNG 导出
            try:
                img_bytes = fig.to_image(format='png', scale=2)
                st.download_button(
                    '导出图表 PNG', data=img_bytes,
                    file_name=f'图表_{selected_q[:5]}.png',
                    mime='image/png', use_container_width=True
                )
            except Exception:
                st.caption('提示：PNG 导出需要 kaleido，若按钮无响应请右键图表另存。')

        with inner_text:
            st.markdown("<h4 style='color:#34495E;margin-bottom:15px;'>📌 选项说明</h4>",
                        unsafe_allow_html=True)
            for short_k, pure_v in legend_dict.items():
                st.markdown(
                    f"<div class='legend-text'><b>{short_k}</b> — {pure_v}</div>",
                    unsafe_allow_html=True
                )
            if others_list:
                st.markdown("<hr style='margin:15px 0 10px 0;'>", unsafe_allow_html=True)
                st.markdown("<h5 style='color:#E67E22;margin-top:10px;'>📝 【其他】补充明细：</h5>",
                            unsafe_allow_html=True)
                for text in set(others_list):
                    st.markdown(
                        f"<div class='legend-text' style='color:#7F8C8D;'>🔹 {text}</div>",
                        unsafe_allow_html=True
                    )

        st.markdown('</div>', unsafe_allow_html=True)
