# chart_builder/factory.py

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from chart_builder.style import apply_style, resolve_color


def _get_series_data(df, series_cfg):
    column = series_cfg["column"]
    if column not in df.columns:
        raise KeyError(f"Spalte '{column}' fehlt im Datensatz.")
    return df[column]


def _add_series(fig, df, series_cfg, x_values):
    values = _get_series_data(df, series_cfg)
    color = resolve_color(series_cfg.get("color", "dark_blue"))
    kind = series_cfg.get("kind",  "line")

    if kind == "line":
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=values,
                mode="lines",
                name=series_cfg.get("label", series_cfg["column"]),
                line=dict(color=color, width=series_cfg.get("line_width", 2)),
                hovertemplate="%{x}<br>%{y}<extra></extra>",
                opacity=0.85,
            )
        )

    elif kind == "bar":
        fig.add_trace(
            go.Bar(
                x=x_values,
                y=values,
                name=series_cfg.get("label", series_cfg["column"]),
                marker=dict(color=color),
                hovertemplate="%{x}<br>%{y}<extra></extra>",
            )
        )

    elif kind == "area":
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=values,
                mode="lines",
                name=series_cfg.get("label", series_cfg["column"]),
                stackgroup=series_cfg.get("stackgroup", "one"),
                line=dict(color=color, width=0),
                hovertemplate="%{x}<br>%{y}<extra></extra>",
                opacity=0.85,
            )
        )

    elif kind == "scatter":
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=values,
                mode="markers",
                name=series_cfg.get("label", series_cfg["column"]),
                marker=dict(color=color, size=8),
                hovertemplate="%{x}<br>%{y}<extra></extra>",
                opacity=0.85,
            )
        )

    else:
        raise ValueError(f"Unsupported chart type: {kind}")

def create_subplots_bar_chart(data, chart_cfg):
    subplot_cfgs = chart_cfg["subplots"]
    fig = make_subplots(
        rows=1,
        cols=len(subplot_cfgs),
        subplot_titles=[item["title"] for item in subplot_cfgs],
        horizontal_spacing=chart_cfg.get("horizontal_spacing", 0.2),
    )

    for col_index, subplot in enumerate(subplot_cfgs, start=1):
        for series in subplot["series"]:
            label = series["label"]
            value = data[series["value"]]
            color = resolve_color(series.get("color", "dark_blue"))

            fig.add_trace(
                go.Bar(
                    y=[label],
                    x=[value],
                    orientation="h",
                    marker=dict(color=color),
                    name=label,
                    showlegend=False,
                ),
                row=1,
                col=col_index,
            )

    fig = apply_style(
        fig,
        title=chart_cfg.get("title"),
        x_title=chart_cfg.get("x_title"),
        y_title=chart_cfg.get("y_title"),
    )

    return fig
def create_chart(data, chart_cfg):
    if chart_cfg.get("multiplot"):
        return create_subplots_bar_chart(data, chart_cfg)

    x_col = chart_cfg.get("x")
    if x_col is None:
        x_values = data.index
    else:
        if x_col not in data.columns:
            raise KeyError(f"X-Achse '{x_col}' fehlt im Datensatz.")
        x_values = data[x_col]

    fig = go.Figure()

    for series_cfg in chart_cfg.get("series", []):
        _add_series(fig, data, series_cfg, x_values)

    fig = apply_style(
        fig,
        title=chart_cfg.get("title"),
        x_title=chart_cfg.get("x_title"),
        y_title=chart_cfg.get("y_title"),
    )
    if chart_cfg.get("barmode"):
        fig.update_layout(barmode=chart_cfg["barmode"])

    return fig