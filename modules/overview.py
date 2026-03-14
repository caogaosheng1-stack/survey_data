"""overview.py — 全局数据概览 Dashboard"""
import streamlit as st
import plotly.express as px
import pandas as pd
from analysis_engine import SurveyEngine


def render(df, colors):
    """概览 Dashboard 主渲染函数。"""

    questions = [q for q in df.columns if '序号' not in q]
    total = len(df)
    n_q = len(questions)

    # ── 题目类型识别 ──
    type_map = {q: SurveyEngine.detect_question_type(df[q]) for q in questions}
    n_multi = sum(1 for t in type_map.values() if t == '多选题')

    # 平均有效率
    valid_rates = [df[q].notna().sum() / total for q in questions]
    avg_valid = sum(valid_rates) / len(valid_rates) * 100 if valid_rates else 0

    # ── 第一行：指标卡 ──
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('📌 总样本量', f'{total} 份')
    c2.metric('🎯 题目数量', f'{n_q} 项')
    c3.metric('✅ 平均有效率', f'{avg_valid:.1f}%')
    c4.metric('🔀 多选题数量', f'{n_multi} 题')

    st.markdown('<br>', unsafe_allow_html=True)

    # ── 第二行：题目概览总表 ──
    st.markdown('### 📋 题目概览总表')
    overview_rows = []
    for q in questions:
        series = df[q]
        valid_n = series.notna().sum()
        missing_rate = (1 - valid_n / total) * 100
        q_type = type_map[q]
        # Top1
        res_df, _ = SurveyEngine.process_question(df, q)
        if res_df is not None and len(res_df) > 0:
            top1_row = res_df.sort_values('频数', ascending=False).iloc[0]
            top1 = f"{top1_row['选项']}（{top1_row['占比(%)']:.1f}%）"
        else:
            top1 = '—'
        overview_rows.append({
            '题目': q,
            '类型': q_type,
            '有效回答': valid_n,
            '缺失率(%)': round(missing_rate, 1),
            'Top 1 选项': top1,
        })
    overview_df = pd.DataFrame(overview_rows)
    st.dataframe(overview_df, use_container_width=True, hide_index=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # ── 第三行：数据质量热力图 ──
    st.markdown('### 🌡️ 数据质量热力图（各题缺失率）')
    missing_vals = [[df[q].isna().sum() / total * 100] for q in questions]
    missing_df = pd.DataFrame(missing_vals, index=questions, columns=['缺失率(%)'])

    fig_heat = px.imshow(
        missing_df.T.values,
        x=questions,
        y=['缺失率(%)'],
        color_continuous_scale='Reds',
        text_auto='.1f',
        aspect='auto',
        zmin=0, zmax=100,
    )
    fig_heat.update_layout(
        height=160,
        plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
        margin=dict(t=10, l=10, r=10, b=80),
        xaxis=dict(tickangle=35, title=''),
        yaxis=dict(title=''),
        coloraxis_colorbar=dict(title='缺失率%'),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # ── 第四行：答题完整度分布 ──
    st.markdown('### 📊 答题完整度分布')
    completeness = df[questions].notna().sum(axis=1) / n_q * 100
    fig_comp = px.histogram(
        completeness, nbins=20,
        labels={'value': '完整度(%)', 'count': '人数'},
        color_discrete_sequence=[colors[0]],
    )
    fig_comp.update_layout(
        height=280,
        plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
        margin=dict(t=10, l=10, r=10, b=40),
        xaxis=dict(title='完整度(%)', range=[0, 105]),
        yaxis=dict(title='人数'),
        showlegend=False,
        bargap=0.05,
    )
    st.plotly_chart(fig_comp, use_container_width=True)
