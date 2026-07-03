"""Jinja filters used to render CV data into LaTeX templates."""

from __future__ import annotations

import re
import textwrap
from typing import Any, Iterable

from mistletoe import Document
from mistletoe.latex_renderer import LaTeXRenderer


_LATEX_REPLACEMENTS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

_LATEX_ESCAPE_PATTERN = re.compile(r"[\\&%$#_{}~^]")


class _LatexFragmentRenderer(LaTeXRenderer):
    """Render Markdown to LaTeX fragments without document wrapper."""

    def render_document(self, token: Any) -> str:
        return self.render_inner(token)


def _as_text(value: Any) -> str:
    """Return a safe string representation used by filters."""

    return "" if value is None else str(value)


# ============================================================================
# Generic text filters
# ============================================================================

def tex(value: Any) -> str:
    """Escape LaTeX special characters in a single, non-recursive pass."""

    return _LATEX_ESCAPE_PATTERN.sub(
        lambda match: _LATEX_REPLACEMENTS[match.group(0)],
        _as_text(value),
    )


def upper_text(value: Any) -> str:
    """Convert text to uppercase."""

    return _as_text(value).upper()


def lower_text(value: Any) -> str:
    """Convert text to lowercase."""

    return _as_text(value).lower()


def soft_wrap(value: Any, width: int = 100) -> str:
    """Wrap long text for readable source output without changing semantics."""

    return textwrap.fill(
        _as_text(value),
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )


# ============================================================================
# Markdown
# ============================================================================

def md_latex(text: Any) -> str:
    """Convert Markdown to LaTeX using mistletoe's LaTeX renderer."""

    with _LatexFragmentRenderer() as renderer:
        return renderer.render(Document(_as_text(text))).strip("\n")


# ============================================================================
# List rendering
# ============================================================================

def lines(values: Iterable[Any] | None) -> str:
    """Convert values into a LaTeX line-separated block."""

    if values is None:
        return ""
    if isinstance(values, str):
        return tex(values)
    return "\\\\\n".join(tex(v) for v in values)


def comma_list(values: Iterable[Any] | None) -> str:
    """Convert values into comma-separated text."""

    if values is None:
        return ""
    if isinstance(values, str):
        return values
    return ", ".join(str(v) for v in values)


# ============================================================================
# CV specific
# ============================================================================

def period(entry: dict[str, Any], lang: str = "de") -> str:
    """Format entry period values (e.g., ``2025-06`` to ``2025/06--heute``)."""

    if "period" in entry and isinstance(entry["period"], dict):
        period_data = entry["period"]
        start_value = period_data["start"]
        end_value = period_data["end"]
    else:
        start_value = entry["start"]
        end_value = entry["end"]

    start = str(start_value).replace("-", "/")
    end = str(end_value)

    if end == "present":
        end = "heute" if lang == "de" else "current"
    else:
        end = end.replace("-", "/")

    return f"{start}--{end}"


def location(profile: dict[str, Any], lang: str = "de") -> str:
    """Build location text like ``Sample City, Germany``."""

    city = profile["address"]["city"]
    country = profile["address"]["country"][lang]
    return f"{city}, {country}"


def full_name(profile: dict[str, Any]) -> str:
    """Build full name text like ``Alex Example``."""

    first = profile["name"]["first"]
    last = profile["name"]["last"]
    return f"{first} {last}"


def postal_city(profile: dict[str, Any]) -> str:
    """Build postal-city text like ``10001 Sample City``."""

    address = profile["address"]
    return f"{address['postal_code']} {address['city']}"


# ============================================================================
# Filter registration
# ============================================================================

def register_filters(env: Any, lang: str = "de") -> Any:
    """Register all custom Jinja filters on the provided environment."""

    env.filters["tex"] = tex
    env.filters["upper_text"] = upper_text
    env.filters["lower_text"] = lower_text
    env.filters["soft_wrap"] = soft_wrap
    env.filters["md_latex"] = md_latex
    env.filters["lines"] = lines
    env.filters["comma_list"] = comma_list
    env.filters["location"] = location
    env.filters["full_name"] = full_name
    env.filters["postal_city"] = postal_city
    env.filters["period"] = period
    return env


__all__ = [
    "tex",
    "upper_text",
    "lower_text",
    "soft_wrap",
    "md_latex",
    "lines",
    "comma_list",
    "period",
    "location",
    "full_name",
    "postal_city",
    "register_filters",
]
