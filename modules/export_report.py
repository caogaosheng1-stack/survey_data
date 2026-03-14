"""export_report.py — 报告导出模块
支持：全题目 Excel 汇总包（每题一个 Sheet）+ 自包含 HTML 交互报告。
"""
import streamlit as st
import pandas as pd
from io import BytesIO
from analysis_engine import SurveyEngine
from modules.chart_builder import build_single_chart
import re


def _extract_letter(text):
    match = re.match(r'^([A-Za-z])[\.、\s]', str(text).strip())
    return match.group(1).upper() if match else None


def _clean_text(text):
    return re.sub(r'^([A-Za-z])[\.、\s]+', '', str(text).strip())


def _build_all_results(df):
    """计算所有题目的频率明细，返回 dict {题目: res_df}。"""
    questions = [q for q in df.columns if '序号' not in q]
    results = {}
    for q in questions:
        res_df, _ = SurveyEngine.process_question(df, q)
        if res_df is not None and len(res_df) > 0:
            results[q] = res_df
    return results


def render(df, colors):
    """报告导出主渲染函数。"""
    st.markdown('### 📥 导出报告')
    st.caption('一键导出所有题目的分析结果，可选 Excel 汇总包或自包含 HTML 交互报告。')

    chart_type_export = st.selectbox(
        'HTML 报告中的图表类型',
        ['柱状图', '条形图', '饼状图', '圆环图', '折线图'],
        key='export_chart_type'
    )

    col_excel, col_html = st.columns(2)

    # ══════════════════
    # Excel 汇总包
    # ══════════════════
    with col_excel:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown('#### 📊 Excel 汇总包')
        st.markdown('每个题目单独一个 Sheet，包含选项、频数、占比。')

        if st.button('生成 Excel 报告', key='gen_excel', use_container_width=True):
            with st.spinner('生成中…'):
                results = _build_all_results(df)
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                    # 首页：概览
                    overview_rows = []
                    for q, res_df in results.items():
                        top1 = res_df.sort_values('频数', ascending=False).iloc[0]
                        overview_rows.append({
                            '题目': q,
                            '有效回答': res_df['频数'].sum(),
                            'Top1 选项': top1['选项'],
                            'Top1 占比(%)': round(top1['占比(%)'], 2),
                            '选项数': len(res_df),
                        })
                    pd.DataFrame(overview_rows).to_excel(
                        writer, sheet_name='概览', index=False
                    )
                    # 每题明细
                    for q, res_df in results.items():
                        sheet_name = q[:28].strip()  # Excel Sheet 名最长 31 字符
                        export_df = res_df[['选项', '频数', '占比(%)']].copy()
                        export_df['占比(%)'] = export_df['占比(%)'].round(2)
                        export_df.to_excel(writer, sheet_name=sheet_name, index=False)

                buf.seek(0)
                st.download_button(
                    '📥 下载 Excel 汇总包',
                    data=buf.getvalue(),
                    file_name='问卷分析汇总.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True
                )
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════
    # HTML 交互报告
    # ══════════════════
    with col_html:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown('#### 🌐 HTML 交互报告')
        st.markdown('含所有题目可交互 Plotly 图表，单文件可直接在浏览器打开。')

        if st.button('生成 HTML 报告', key='gen_html', use_container_width=True):
            with st.spinner('生成中，题目较多时请稍候…'):
                results = _build_all_results(df)
                html_parts = [
                    """
                    <!DOCTYPE html><html lang="zh-CN"><head>
                    <meta charset="UTF-8">
                    <title>屿寻摄影·问卷分析报告</title>
                    <style>
                      body{font-family:'Microsoft YaHei',sans-serif;background:#F4F6F9;
                           color:#2C3E50;max-width:1100px;margin:0 auto;padding:24px;}
                      h1{color:#FF69B4;text-align:center;margin-bottom:8px;}
                      .q-block{background:#fff;border-radius:12px;padding:20px;
                               margin-bottom:24px;box-shadow:0 4px 12px rgba(0,0,0,.05);}
                      .q-title{font-size:16px;font-weight:700;margin-bottom:12px;
                                color:#34495E;border-left:4px solid #1890FF;
                                padding-left:10px;}
                    </style></head><body>
                    <h1>📒 屿寻摄影·智能问卷分析报告</h1>
                    <p style="text-align:center;color:#7F8C8D;">
                      共 {total} 份问卷 · {n_q} 个题目</p>
                    """.format(total=len(df), n_q=len(results))
                ]

                for q, res_df in results.items():
                    # 标号处理
                    res_df = res_df.copy()
                    res_df['现有标号'] = res_df['选项'].apply(_extract_letter)
                    existing = res_df['现有标号'].dropna().tolist()
                    next_c = ord(max(existing)) + 1 if existing else ord('A')
                    labels = []
                    for v in res_df['现有标号']:
                        if pd.notna(v):
                            labels.append(v)
                        else:
                            labels.append(chr(next_c))
                            next_c += 1
                    res_df['简称'] = labels
                    res_df['纯净解释'] = res_df['选项'].apply(_clean_text)
                    res_df = res_df.sort_values('简称').reset_index(drop=True)

                    fig = build_single_chart(res_df, chart_type_export, colors, title=q)
                    fig_html = fig.to_html(
                        full_html=False, include_plotlyjs='cdn',
                        config={'displayModeBar': False}
                    )
                    html_parts.append(
                        f'<div class="q-block">'
                        f'<div class="q-title">{q}</div>'
                        f'{fig_html}</div>'
                    )

                html_parts.append('</body></html>')
                html_str = '\n'.join(html_parts)
                html_bytes = html_str.encode('utf-8')

                st.download_button(
                    '📥 下载 HTML 报告',
                    data=html_bytes,
                    file_name='问卷分析报告.html',
                    mime='text/html',
                    use_container_width=True
                )
        st.markdown('</div>', unsafe_allow_html=True)
