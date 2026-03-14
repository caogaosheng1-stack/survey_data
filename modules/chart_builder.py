"""chart_builder.py — 统一图表工厂
所有 plotly 图表生成逻辑集中在此。
修复：雷达图少于3选项崩溃、交叉分析加折线图、关闭动画提升渲染速度。
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# 统一关闭动画，提升切换速度
_NO_ANIM = dict(transition={'duration': 0})


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
            legend=dict(orientation='h', yanchor='top', y=-0.1,
                        xanchor='center', x=0.5, font=dict(size=12)),
            showlegend=True,
            margin=dict(t=30, l=10, r=10, b=60),
            height=430,
            plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
            font=dict(family='Microsoft YaHei, PingFang SC, sans-serif', size=13),
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
        apply_base_style(fig)

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
        apply_base_style(fig)

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
        apply_base_style(fig)

    elif chart_type == '雷达图':
        categories = res_df['纯净解释'].tolist()
        values = res_df['占比(%)'].tolist()

        if len(categories) < 3:
            # 选项不足3个，降级为柱状图并提示
            fig = px.bar(res_df, x='纯净解释', y='占比(%)', text=formatted_text,
                         title=f'{title}（选项<3，已自动切换柱状图）')
            fig.update_traces(marker_color=c_main, textposition='outside',
                              textfont=dict(size=13, weight='bold'), width=0.45)
            fig.update_layout(
                yaxis=dict(tickvals=[0, 25, 50, 75], range=y_range, title=''),
                xaxis=dict(tickangle=45, title=''), showlegend=False,
            )
            apply_base_style(fig)
        else:
            # 闭合雷达图（首尾相连）
            cats_closed = categories + [categories[0]]
            vals_closed = values + [values[0]]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=vals_closed,
                theta=cats_closed,
                fill='toself',
                fillcolor=c_main + '55',
                line=dict(color=c_main, width=2),
                marker=dict(size=7, color=c_main),
                name='占比(%)'
            ))
            fig.update_layout(
                height=430,
                plot_bgcolor='#FFFFFF',
                paper_bgcolor='#FFFFFF',
                font=dict(family='Microsoft YaHei, PingFang SC, sans-serif', size=13),
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(80, max_pct * 1.2)],
                        tickfont=dict(size=11),
                    ),
                    bgcolor='#FFFFFF',
                ),
                showlegend=False,
                title=title,
                margin=dict(t=50, l=40, r=40, b=40),
            )

    else:
        # fallback
        fig = px.bar(res_df, x='纯净解释', y='占比(%)', text=formatted_text, title=title)
        fig.update_traces(marker_color=c_main, textposition='outside')
        apply_base_style(fig)

    return fig


# ──────────────────────────────────────────
# 交叉图表
# ──────────────────────────────────────────
def build_cross_chart(cross_df, chart_type, colors):
    """
    生成交叉分析图表。
    chart_type: 分组柱状图 | 堆叠柱状图 | 热力图 | 气泡图 | 折线图
    """
    df_plot = cross_df.reset_index()
    row_label = df_plot.columns[0]
    value_cols = df_plot.columns[1:].tolist()
    df_melted = df_plot.melt(
        id_vars=row_label, value_vars=value_cols,
        var_name='列变量', value_name='值'
    )

    if chart_type == '分组柱状图':
        fig = px.bar(
            df_melted, x=row_label, y='值', color='列变量',
            barmode='group', color_discrete_sequence=colors,
            text=df_melted['值'].apply(lambda v: f'{v:.1f}')
        )
        fig.update_traces(textposition='outside', textfont=dict(size=11))
        fig.update_layout(
            xaxis=dict(tickangle=30, title=''),
            yaxis=dict(title=''), legend_title=''
        )

    elif chart_type == '堆叠柱状图':
        fig = px.bar(
            df_melted, x=row_label, y='值', color='列变量',
            barmode='relative', color_discrete_sequence=colors,
            text=df_melted['值'].apply(lambda v: f'{v:.1f}')
        )
        fig.update_traces(textposition='inside', textfont=dict(size=11))
        fig.update_layout(
            xaxis=dict(tickangle=30, title=''),
            yaxis=dict(title=''), legend_title=''
        )

    elif chart_type == '热力图':
        fig = px.imshow(
            cross_df.values,
            x=cross_df.columns.tolist(),
            y=cross_df.index.tolist(),
            color_continuous_scale='Blues',
            text_auto='.1f',
            aspect='auto',
        )
        fig.update_layout(
            xaxis=dict(tickangle=30, title=''),
            yaxis=dict(title='')
        )

    elif chart_type == '气泡图':
        # 避免 size=0 导致报错
        df_melted['值_safe'] = df_melted['值'].clip(lower=0.01)
        fig = px.scatter(
            df_melted, x=row_label, y='列变量',
            size='值_safe', color='列变量',
            color_discrete_sequence=colors,
            size_max=60,
            text=df_melted['值'].apply(lambda v: f'{v:.1f}')
        )
        fig.update_traces(textposition='top center', textfont=dict(size=11))
        fig.update_layout(
            xaxis=dict(tickangle=30, title=''),
            yaxis=dict(title=''), legend_title=''
        )

    elif chart_type == '折线图':
        fig = px.line(
            df_melted, x=row_label, y='值', color='列变量',
            color_discrete_sequence=colors,
            markers=True,
            text=df_melted['值'].apply(lambda v: f'{v:.1f}')
        )
        fig.update_traces(
            textposition='top center', textfont=dict(size=11),
            marker=dict(size=8), line=dict(width=2.5)
        )
        fig.update_layout(
            xaxis=dict(tickangle=30, title=''),
            yaxis=dict(title=''), legend_title=''
        )

    else:
        fig = px.bar(
            df_melted, x=row_label, y='值', color='列变量',
            barmode='group', color_discrete_sequence=colors
        )

    apply_base_style(fig, height=450)
    return fig
