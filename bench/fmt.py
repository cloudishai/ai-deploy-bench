"""Formatting helpers for the markdown reports."""

from __future__ import annotations

DASH = "—"


def duration(seconds: float | None) -> str:
    if seconds is None:
        return DASH
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def tokens(count: float | None) -> str:
    if count is None:
        return DASH
    if count >= 1_000_000:
        return f"{count / 1_000_000:.2f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(int(count))


def usd(amount: float | None, approximate: bool = False) -> str:
    if amount is None:
        return DASH
    return ("~" if approximate else "") + f"${amount:,.2f}"


def count(value: int | None) -> str:
    return DASH if value is None else str(value)


def minutes(value: float | None) -> str:
    return DASH if value is None else f"{value:g} min"


def score(value: float | None) -> str:
    return DASH if value is None else f"{value:.0f}/100"


def pct(fraction: float | None) -> str:
    return DASH if fraction is None else f"{fraction:.0%}"


def cell(text: object) -> str:
    """Escapes a value for a markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ")


STATUS_ICONS = {"success": "✅", "partial": "⚠️", "failed": "❌", "error": "💥", "missing": "❔", "human": "🙋"}


def status(value: str) -> str:
    return STATUS_ICONS.get(value, "❔")
