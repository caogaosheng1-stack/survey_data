"""stat_analysis.py — 统计检验模块
卡方独立性检验（含 Cramer's V）、Pearson 相关系数热力图、均值对比图。
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from analysis_engine import SurveyEngine


def render(df, colors):
    """统计检验主渲染函数。"""
    questions = [q for q in df.columns if '序号' not in q]

    tab_chi2, tab_corr, tab_mean = st.tabs(['📐 卡方独立性检验', '🔗 相关系数矩阵', '📊 均值对比'])

    # ══════════════════════════════════════
    # Tab1：卡方检验
    # ══════════════════════════════════════
    with tab_chi2:
        st.markdown('#### 卡方独立性检验')
        st.caption('判断两个分类变量之间是否存在显著关联。')

        c1, c2 = st.columns(2)
        with c1:
            q1 = st.selectbox('变量 A', questions, key='chi2_q1')
        with c2:
            q2 = st.selectbox('变量 B', questions,
                              index=min(1, len(questions)-1), key='chi2_q2')

        if q1 == q2:
            st.warning('请选择两个不同的变量。')
        else:
            if st.button('▶ 执行卡方检验', key='chi2_run', use_container_width=True):
                try:
                    freq_df, _, _ = SurveyEngine.build_crosstab(df, q1, q2)
                    if freq_df.empty or freq_df.shape[0] < 2 or freq_df.shape[1] < 2:
                        st.warning('交叉表过小（至少需要 2×2），无法执行检验。')
                    else:
                        result = SurveyEngine.chi2_test(freq_df)

                        # 结果卡片（左图右字 布局，方便截图）
                        left, right = st.columns([1, 1.2], gap='large')

                        with left:
                            st.markdown('<div class="report-card">', unsafe_allow_html=True)
                            st.markdown('##### 交叉频数表')
                            st.dataframe(
                                freq_df.style.highlight_max(axis=None, color='#d4edff'),
                                use_container_width=True
                            )
                            st.markdown('</div>', unsafe_allow_html=True)

                        with right:
                            st.markdown('<div class="report-card">', unsafe_allow_html=True)
                            st.markdown('##### 检验结果')

                            m1, m2, m3 = st.columns(3)
                            m1.metric('χ² 值', result['chi2'])
                            m2.metric('自由度', result['dof'])
                            m3.metric('p 值', result['p'])

                            strength_color = {
                                '弱': '#95A5A6', '中': '#F39C12', '强': '#E74C3C'
                            }.get(result['strength'], '#95A5A6')

                            st.markdown(
                                f"""
                                <div style='margin-top:16px;padding:14px 18px;
                                     background:#F8F9FA;border-radius:10px;
                                     border-left:5px solid {strength_color};'>
                                  <b>Cramer's V</b>：{result['cramers_v']}&nbsp;&nbsp;
                                  <span style='color:{strength_color};font-weight:700;'>
                                    [{result['strength']}关联]
                                  </span><br><br>
                                  <span style='font-size:14px;'>{result['conclusion']}</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            st.markdown('</div>', unsafe_allow_html=True)

                except Exception as e:
                    st.error(f'检验失败：{e}')

    # ══════════════════════════════════════
    # Tab2：相关系数矩阵
    # ══════════════════════════════════════
    with tab_corr:
        st.markdown('#### Pearson 相关系数矩阵')
        st.caption('适用于数值型题目（如满意度评分）。无法转换为数字的题目将自动跳过。')

        selected_qs = st.multiselect(
            '选择参与计算的题目（至少 2 个）', questions,
            default=questions[:min(5, len(questions))], key='corr_qs'
        )
        threshold = st.slider('只显示绝对值 ≥ 阈值的相关系数', 0.0, 1.0, 0.0, 0.05, key='corr_thresh')

        if len(selected_qs) < 2:
            st.info('请至少选择 2 个题目。')
        elif st.button('▶ 计算相关系数', key='corr_run', use_container_width=True):
            corr = SurveyEngine.correlation_matrix(df, selected_qs)
            if corr is None:
                st.warning('选中的题目中数值型数据不足，无法计算相关系数矩阵。')
            else:
                # 应用阈值遮罩
                masked = corr.copy()
                masked[masked.abs() < threshold] = np.nan

                fig = px.imshow(
                    masked,
                    color_continuous_scale='RdBu_r',
                    zmin=-1, zmax=1,
                    text_auto='.2f',
                    aspect='auto',
                )
                fig.update_layout(
                    height=max(350, len(corr) * 55),
                    plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
                    margin=dict(t=20, l=10, r=10, b=60),
                    xaxis=dict(tickangle=35),
                    coloraxis_colorbar=dict(title='r'),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(corr.style.format('{:.3f}').background_gradient(
                    cmap='RdBu_r', vmin=-1, vmax=1),
                    use_container_width=True
                )

    # ══════════════════════════════════════
    # Tab3：均值对比
    # ══════════════════════════════════════
    with tab_mean:
        st.markdown('#### 均值对比图')
        st.caption('适用于李克特量表题（选项为数字或可转换为数值的评分题），按分组变量展示各组均值。')

        mc1, mc2 = st.columns(2)
        with mc1:
            group_q = st.selectbox('分组变量', questions, key='mean_group')
        with mc2:
            value_q = st.selectbox('量表题（数值型）', questions,
                                   index=min(1, len(questions)-1), key='mean_value')

        if st.button('▶ 生成均值对比', key='mean_run', use_container_width=True):
            result_df = SurveyEngine.group_mean(df, group_q, value_q)
            if result_df is None or len(result_df) == 0:
                st.warning('该题目无法转换为数值，请选择评分类题目。')
            else:
                # 左表 右图
                left, right = st.columns([1, 1.5], gap='large')
                with left:
                    st.markdown('<div class="report-card">', unsafe_allow_html=True)
                    st.markdown('##### 各组均值明细')
                    st.dataframe(result_df.style.format({'均值': '{:.3f}', '标准差': '{:.3f}'}),
                                 use_container_width=True, hide_index=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with right:
                    st.markdown('<div class="report-card">', unsafe_allow_html=True)
                    st.markdown('##### 均值对比图（含误差棒）')
                    fig = go.Figure()
                    for i, row in result_df.iterrows():
                        fig.add_trace(go.Bar(
                            x=[row['分组']],
                            y=[row['均值']],
                            error_y=dict(
                                type='data',
                                array=[row['标准差']],
                                visible=True,
                                color='#555',
                                thickness=2,
                                width=8,
                            ),
                            marker_color=colors[i % len(colors)],
                            name=str(row['分组']),
                            text=f"{row['均值']:.2f}",
                            textposition='outside',
                        ))
                    fig.update_layout(
                        height=380,
                        plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
                        margin=dict(t=20, l=10, r=10, b=40),
                        xaxis=dict(title='', tickangle=30),
                        yaxis=dict(title='均值'),
                        showlegend=False,
                        bargap=0.35,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
