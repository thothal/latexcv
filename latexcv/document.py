"""Normalized document models for CV content and layout."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Block:
    """Reusable content block keyed by a globally unique ID."""

    id: str
    kind: str
    title: dict[str, str] | None = None
    items: list[dict[str, Any]] | None = None
    text: dict[str, str] | None = None
    source: dict[str, Any] | None = None
    options: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LayoutPlacement:
    """Placement of one block inside one page region."""

    block: str
    renderer: str
    item_include: list[str] | None = None
    item_exclude: list[str] | None = None
    item_order: list[str] | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PageSpec:
    """One layout page with settings and region placements."""

    id: str
    settings: dict[str, Any]
    regions: dict[str, list[LayoutPlacement]]


@dataclass(frozen=True)
class LayoutSpec:
    """Top-level layout specification."""

    version: int
    pages: list[PageSpec]
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RenderUnit:
    """Renderer-ready unit passed to the template layer."""

    block_id: str
    renderer: str
    title: str | None
    data: dict[str, Any]


@dataclass(frozen=True)
class RenderPage:
    """A fully normalized page ready for final template rendering."""

    id: str
    settings: dict[str, Any]
    regions: dict[str, list[RenderUnit]]


@dataclass(frozen=True)
class RenderDocument:
    """Normalized render document assembled from blocks and layout."""

    lang: str
    profile: dict[str, Any]
    pages: list[RenderPage]
    settings: dict[str, Any] = field(default_factory=dict)