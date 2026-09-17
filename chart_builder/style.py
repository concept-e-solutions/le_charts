# chart_builder/style.py

from __future__ import annotations
import yaml
from pathlib import Path

STYLE_FILE = Path(__file__).resolve().parents[1] / "config" / "style.yml"

def load_style():
    with open(STYLE_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)

STYLE = load_style()

COLORS = STYLE["colors"]
PLOT = STYLE["plot"]

def resolve_color(name):
    if name in COLORS:
        return COLORS[name]
    return name

def apply_style(fig, title=None, x_title=None, y_title=None):
    fig.update_layout(
        template="plotly_white",
        title={"text": title, "x": 0.5} if title else None,
        font=dict(
            family=PLOT["font_family"],
            size=PLOT["font_size"],
            #color=COLORS["text"],
        ),
        width=PLOT["width"],
        height=PLOT["height"],
        margin=dict(
            l=PLOT["margins"]["left"],
            r=PLOT["margins"]["right"],
            t=PLOT["margins"]["top"],
            b=PLOT["margins"]["bottom"],
        ),
        hovermode="x unified",
    )

    fig.update_xaxes(
        title=x_title,
        showgrid=True,
        gridcolor=COLORS["grid"],
        ticklabelstandoff = 5,
    )
    fig.update_yaxes(
        title=y_title,
        showgrid=True,
        gridcolor=COLORS["grid"],
        ticklabelstandoff = 5,
    )

    return fig