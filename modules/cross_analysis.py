"""cross_analysis.py — 交叉分析模块
支持两变量交叉 + 第三维度过滤，多选题自动 explode，5 种可视化图表。
"""
import streamlit as st
import pandas as pd
from analysis_engine import SurveyEngine
from modules.chart_builder import build_cross_chart


def render(df, colors):
    """交叉分析主渲染函数。"""
    questions = [q for q in df.columns if '序号' not in q]

    st.markdown('### 🔀 交叉分析')
    st.caption('选择两个题目进行交叉分析，可选第三维度作为过滤条件。多选题将自动拆分展开后计算。')

    # ── 快捷场景预设 ──
    preset_col1, preset_col2, preset_col3 = st.columns(3)
    preset_row = None
    with preset_col1:
        if st.button('👫 性别 × …', use_container_width=True):
            gender_candidates = [q for q in questions if '性别' in q or 'gender' in q.lower()]
            if gender_candidates:
                preset_row = gender_candidates[0]
    with preset_col2:
        if st.button('🎂 年龄 × …', use_container_width=True):
            age_candidates = [q for q in questions if '年龄' in q or 'age' in q.lower()]
            if age_candidates:
                preset_row = age_candidates[0]
    with preset_col3:
        st.caption('或手动选择下方变量')

    st.markdown('<hr style="margin:10px 0;">', unsafe_allow_html=True)

    # ── 变量选择 ──
    sel_col1, sel_col2, sel_col3 = st.columns(3)
    with sel_col1:
        row_default = questions.index(preset_row) if preset_row and preset_row in questions else 0
        row_col = st.selectbox('行变量（分组依据）', questions, index=row_default, key='cross_row')
    with sel_col2:
        col_default = 1 if len(questions) > 1 else 0
        col_col = st.selectbox('列变量（分析目标）', questions, index=col_default, key='cross_col')
    with sel_col3:
        filter_options = ['（不过滤）'] + questions
        filter_col_sel = st.selectbox('第三维度过滤变量', filter_options, key='cross_filter_col')
        filter_col = None if filter_col_sel == '（不过滤）' else filter_col_sel

    # 第三维度过滤值
    filter_val = None
    if filter_col:
        filter_vals = sorted(df[filter_col].dropna().unique().tolist())
        filter_val = st.selectbox(f'过滤值（{filter_col}）', filter_vals, key='cross_filter_val')

    # ── 展示类型 & 图表类型 ──
    disp_col, chart_col = st.columns(2)
    with disp_col:
        table_mode = st.radio(
            '展示类型', ['频数', '行百分比(%)', '列百分比(%)'],
            horizontal=True, key='cross_table_mode'
        )
    with chart_col:
        chart_type = st.radio(
            '图表类型', ['分组柱状图', '堆叠柱状图', '热力图', '气泡图', '折线图'],
            horizontal=True, key='cross_chart_type'
        )

    if row_col == col_col:
        st.warning('行变量和列变量不能相同，请重新选择。')
        return

    # ── 计算交叉表 ──
    try:
        freq_df, row_pct_df, col_pct_df = SurveyEngine.build_crosstab(
            df, row_col, col_col,
            filter_col=filter_col, filter_val=filter_val
        )
    except Exception as e:
        st.error(f'交叉分析计算失败：{e}')
        return

    if freq_df.empty:
        st.warning('过滤后无数据，请调整过滤条件。')
        return

    # 根据展示类型选择数据
    display_map = {
        '频数': freq_df,
        '行百分比(%)': row_pct_df,
        '列百分比(%)': col_pct_df,
    }
    show_df = display_map[table_mode]

    # ── 左表 右图 布局（与单题分析保持一致，方便截图）──
    left, right = st.columns([1, 1.6], gap='large')

    with left:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        filter_note = f'（已过滤：{filter_col} = {filter_val}）' if filter_col else ''
        st.markdown(f'#### 📋 交叉表 — {table_mode}{filter_note}')
        if table_mode == '频数':
            st.dataframe(show_df.style.highlight_max(axis=None, color='#d4edff'),
                         use_container_width=True)
        else:
            st.dataframe(show_df.style.format('{:.1f}%').background_gradient(cmap='Blues'),
                         use_container_width=True)
        csv_bytes = show_df.reset_index().to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            '📥 导出交叉表 CSV', data=csv_bytes,
            file_name=f'交叉_{row_col[:4]}x{col_col[:4]}.csv',
            use_container_width=True
        )
        if filter_col:
            st.caption(f'注：已按「{filter_col} = {filter_val}」过滤，多选题已拆分展开，合计可能超过总样本量。')
        else:
            st.caption('注：多选题已拆分展开，合计可能超过总样本量。')
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown(f'#### 📊 {chart_type} — {row_col[:15]} × {col_col[:15]}')
        chart_df = freq_df if table_mode == '频数' else (
            row_pct_df if table_mode == '行百分比(%)' else col_pct_df
        )
        try:
            fig = build_cross_chart(chart_df, chart_type, colors)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f'图表生成失败：{e}')
        st.markdown('</div>', unsafe_allow_html=True)
