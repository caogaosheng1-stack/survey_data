"""chart_builder.py — 统一图表工厂
所有 plotly 图表生成逻辑集中在此，对外暴露 build_single_chart / build_cross_chart / apply_base_style。
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# ──────────────────────────────────────────
# 基础样式
# ──────────────────────────────────────────
def apply_base_style(fig, height=430):
    """为任意 Figure 应用统一白底样式。"""
    fig.update_layout(
        height=height,
        plot_bgcolor='#FFFFFF',
        paper_bgcolor='#FFFFFF',
        font=dict(family='Microsoft YaHei, PingFang SC, sans-serif', size=13),
        margin=dict(t=30, l=10, r=10, b=10),
        xaxis=dict(showgrid=True, gridcolor='#F0F2F6'),
        yaxis=dict(showgrid=True, gridcolor='#F0F2F6'),
    )
    return fig


# ──────────────────────────────────────────
# 单题图表
# ──────────────────────────────────────────
def build_single_chart(res_df, chart_type, colors, title=''):
    """
    生成单题分析图表。
    chart_type: 饼状图 | 圆环图 | 柱状图 | 条形图 | 折线图 | 雷达图
    """
    c_main = colors[0]
    max_pct = res_df['占比(%)'].max()
    y_range = [0, max(80, max_pct * 1.15)]
    formatted_text = res_df['占比(%)'].apply(lambda x: f'{x:.2f}%')

    if chart_type in ('饼状图', '圆环图'):
        hole = 0.45 if chart_type == '圆环图' else 0
        fig = px.pie(
            res_df, names='纯净解释', values='频数',
            hole=hole, color_discrete_sequence=colors, title=title
        )
        fig.update_traces(
            text=formatted_text, textinfo='text', textposition='outside',
            marker=dict(line=dict(color='#FFFFFF', width=1.5)),
            insidetextorientation='horizontal',
        )
        fig.update_layout(
            legend=dict(orientation='h', yanchor='top', y=-0.1, xanchor='center', x=0.5, font=dict(size=12)),
            showlegend=True,
            margin=dict(t=30, l=10, r=10, b=60),
        )

    elif chart_type == '柱状图':
        fig = px.bar(res_df, x='纯净解释', y='占比(%)', text=formatted_text, title=title)
        fig.update_traces(
            marker_color=c_main, textposition='outside',
            textfont=dict(size=13, weight='bold'), width=0.45
        )
        fig.update_layout(
            yaxis=dict(tickvals=[0, 25, 50, 75], range=y_range, title=''),
            xaxis=dict(tickangle=45, title=''), showlegend=False,
        )

    elif chart_type == '条形图':
        fig = px.bar(
            res_df, x='占比(%)', y='纯净解释', text=formatted_text,
            orientation='h', title=title
        )
        fig.update_traces(
            marker_color=c_main, textposition='outside',
            textfont=dict(size=13, weight='bold'), width=0.45
        )
        fig.update_layout(
            xaxis=dict(tickvals=[0, 25, 50, 75], range=y_range, title=''),
            yaxis=dict(autorange='reversed', title=''), showlegend=False,
        )

    elif chart_type == '折线图':
        fig = px.line(
            res_df, x='纯净解释', y='占比(%)', text=formatted_text,
            markers=True, title=title
        )
        fig.update_traces(
            line=dict(color=c_main, width=3),
            marker=dict(size=10, color=c_main, line=dict(color='white', width=1.5)),
            textposition='top center', textfont=dict(size=13, weight='bold'),
        )
        fig.update_layout(
            yaxis=dict(tickvals=[0, 25, 50, 75], range=y_range, title=''),
            xaxis=dict(tickangle=45, title=''), showlegend=False,
        )

    elif chart_type == '雷达图':
        categories = res_df['纯净解释'].tolist()
        values = res_df['占比(%)'].tolist()
        # 闭合雷达图
        categories += [categories[0]]
        values += [values[0]]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values, theta=categories,
            fill='toself', fillcolor=c_main + '55',
            line=dict(color=c_main, width=2),
            marker=dict(size=7, color=c_main),
            name='占比(%)'
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, max(80, max_pct * 1.2)]),
                bgcolor='#FFFFFF',
            ),
            showlegend=False,
            title=title,
        )

    else:
        # fallback 柱状图
        fig = px.bar(res_df, x='纯净解释', y='占比(%)', text=formatted_text, title=title)
        fig.update_traces(marker_color=c_main, textposition='outside')

    if chart_type not in ('饼状图', '圆环图', '雷达图'):
        apply_base_style(fig)
    else:
        fig.update_layout(
            height=430, plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
            font=dict(family='Microsoft YaHei, PingFang SC, sans-serif', size=13),
        )
    return fig


# ──────────────────────────────────────────
# 交叉图表
# ──────────────────────────────────────────
def build_cross_chart(cross_df, chart_type, colors):
    """
    生成交叉分析图表。
    cross_df: 行=行变量类别, 列=列变量类别, 值=频数或百分比
    chart_type: 分组柱状图 | 堆叠柱状图 | 热力图 | 气泡图
    """
    df_plot = cross_df.reset_index()
    row_label = df_plot.columns[0]
    value_cols = df_plot.columns[1:].tolist()
    df_melted = df_plot.melt(id_vars=row_label, value_vars=value_cols,
                             var_name='列变量', value_name='值')

    if chart_type == '分组柱状图':
        fig = px.bar(
            df_melted, x=row_label, y='值', color='列变量',
            barmode='group', color_discrete_sequence=colors,
            text=df_melted['值'].apply(lambda v: f'{v:.1f}')
        )
        fig.update_traces(textposition='outside', textfont=dict(size=11))
        fig.update_layout(xaxis=dict(tickangle=30, title=''), yaxis=dict(title=''), legend_title='')

    elif chart_type == '堆叠柱状图':
        fig = px.bar(
            df_melted, x=row_label, y='值', color='列变量',
            barmode='relative', color_discrete_sequence=colors,
            text=df_melted['值'].apply(lambda v: f'{v:.1f}')
        )
        fig.update_traces(textposition='inside', textfont=dict(size=11))
        fig.update_layout(xaxis=dict(tickangle=30, title=''), yaxis=dict(title=''), legend_title='')

    elif chart_type == '热力图':
        fig = px.imshow(
            cross_df.values,
            x=cross_df.columns.tolist(),
            y=cross_df.index.tolist(),
            color_continuous_scale='Blues',
            text_auto='.1f',
            aspect='auto',
        )
        fig.update_layout(xaxis=dict(tickangle=30, title=''), yaxis=dict(title=''))

    elif chart_type == '气泡图':
        fig = px.scatter(
            df_melted, x=row_label, y='列变量', size='值',
            color='列变量', color_discrete_sequence=colors,
            size_max=60,
            text=df_melted['值'].apply(lambda v: f'{v:.1f}')
        )
        fig.update_traces(textposition='top center', textfont=dict(size=11))
        fig.update_layout(xaxis=dict(tickangle=30, title=''), yaxis=dict(title=''), legend_title='')

    else:
        fig = px.bar(df_melted, x=row_label, y='值', color='列变量',
                     barmode='group', color_discrete_sequence=colors)

    apply_base_style(fig, height=450)
    return fig
