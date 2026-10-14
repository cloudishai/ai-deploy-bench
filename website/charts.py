"""SVG charts, rendered at build time so pages need no charting library and no inline styles.

Colors come from CSS classes (`c0`, `c1`, ...), so a chart follows the page's light or dark theme.
"""

from __future__ import annotations

import math
from typing import Callable, Sequence

from markupsafe import Markup, escape

from website.data import Series

WIDTH, HEIGHT = 640, 300
LEFT, RIGHT, TOP, BOTTOM = 60, 18, 18, 46
MAX_X_LABELS = 8
DODGE = 9.0  # px between series at the same run


def nice_ceiling(value: float) -> float:
    """The smallest of 1, 2, 2.5 or 5 times a power of ten that is at least `value`."""
    if value <= 0:
        return 1.0
    power = 10 ** math.floor(math.log10(value))
    return next(m * power for m in (1, 2, 2.5, 5, 10) if value <= m * power + 1e-9)


def line_chart(labels: Sequence[str], series: Sequence[Series], value: Callable[[float | None], str],
               tick: Callable[[float], str], title: str, top: float | None = None, integer: bool = False) -> Markup:
    """One line per series over `labels` (runs); gaps where a series has no value. Series are nudged
    apart horizontally so equal values stay visible."""
    known = [v for s in series for v in s.values if v is not None]
    if not known:
        return Markup(
            f'<svg class="chart chart-empty" viewBox="0 0 {WIDTH} {HEIGHT // 2}" role="img" aria-label="{escape(title)}: no data">'
            f'<text x="{WIDTH / 2}" y="{HEIGHT / 4}" text-anchor="middle" class="empty">No data yet</text></svg>')
    if top is not None:
        ceiling = top
    elif integer:
        ceiling = float(max(4, math.ceil(max(known) * 1.08 / 4) * 4))
    else:
        ceiling = nice_ceiling(max(known) * 1.08)
    plot_w, plot_h = WIDTH - LEFT - RIGHT, HEIGHT - TOP - BOTTOM
    nudge = min(DODGE, plot_w / len(labels) / (len(series) + 1))

    def x(i: int, k: int | None = None) -> float:
        center = LEFT + (i + 0.5) * plot_w / len(labels)
        return center if k is None else center + (k - (len(series) - 1) / 2) * nudge

    def y(v: float) -> float:
        return TOP + plot_h * (1 - min(v, ceiling) / ceiling)

    parts = [f'<svg class="chart" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{escape(title)}">']
    for step in range(5):
        level = ceiling * step / 4
        parts.append(f'<line class="grid" x1="{LEFT}" x2="{WIDTH - RIGHT}" y1="{y(level):.1f}" y2="{y(level):.1f}"/>'
                     f'<text class="tick" x="{LEFT - 8}" y="{y(level) + 4:.1f}" text-anchor="end">{escape(tick(level))}</text>')
    every = max(1, math.ceil(len(labels) / MAX_X_LABELS))
    for i, label in enumerate(labels):
        if i % every == 0 or i == len(labels) - 1:
            parts.append(f'<text class="tick" x="{x(i):.1f}" y="{HEIGHT - BOTTOM + 22}" text-anchor="middle">{escape(label)}</text>')
    for k, s in enumerate(series):
        parts.append(f'<g class="series c{s.color % 8}" data-series="{escape(s.key)}">')
        segment: list[str] = []
        for i, v in enumerate(list(s.values) + [None]):
            if v is not None:
                segment.append(f"{x(i, k):.1f},{y(v):.1f}")
            elif segment:
                if len(segment) > 1:
                    parts.append(f'<polyline class="line" points="{" ".join(segment)}"/>')
                segment = []
        for i, v in enumerate(s.values):
            if v is not None:
                parts.append(f'<circle class="dot" cx="{x(i, k):.1f}" cy="{y(v):.1f}" r="5">'
                             f'<title>{escape(s.name)} · {escape(labels[i])}: {escape(value(v))}</title></circle>')
        parts.append("</g>")
    parts.append("</svg>")
    return Markup("".join(parts))


def bar(fraction: float | None, css: str = "") -> Markup:
    """A thin horizontal bar filled to `fraction` (0-1), for scores in tables."""
    filled = 0.0 if fraction is None else max(0.0, min(1.0, fraction)) * 100
    return Markup(f'<svg class="bar {escape(css)}" viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true">'
                  f'<rect class="track" width="100" height="8" rx="4"/>'
                  f'<rect class="fill" width="{filled:.1f}" height="8" rx="4"/></svg>')
