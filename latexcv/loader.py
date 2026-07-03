"""Load CV YAML data used by the rendering pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import re
from typing import Any

import yaml

from .document import Block, LayoutPlacement, LayoutSpec, PageSpec, RenderDocument, RenderPage, RenderUnit


_DEFAULT_LAYOUT_FILENAME = "layout.yaml"
_SUPPORTED_REGIONS = {"header", "body", "sidebar"}
_ALLOWED_BLOCK_KEYS = {"kind", "title", "items", "text", "source", "options", "data"}
_SUPPORTED_CONTACT_TYPES = {"location", "phone", "email", "website", "linkedin", "github", "stackoverflow"}
_SUPPORTED_COLOR_OVERRIDES = {
    "panel_background",
    "panel_foreground",
    "footer_background",
    "footer_foreground",
    "page_background",
    "page_foreground",
    "section_marker",
    "timeline_meta",
    "accent",
}
_RENDERER_COMPATIBILITY = {
    "profile_header": {"profile"},
    "quote": {"quote"},
    "timeline": {"timeline"},
    "contact_list": {"list"},
    "icon_text_list": {"list"},
    "comma_list": {"list"},
    "rating_list": {"list"},
    "language_list": {"list"},
    "icon_grid": {"list"},
    "qr_asset": {"asset"},
    "plain_text": {"text"},
}


class LayoutValidationError(ValueError):
    """Raised when the layout or block registry is invalid."""


def _as_mapping(value: Any, source: Path) -> dict[str, Any]:
    """Return YAML content as mapping and fail fast for invalid shapes."""

    if isinstance(value, dict):
        return value
    raise ValueError(f"Expected mapping in '{source}', got {type(value).__name__}.")


def _as_mapping_value(value: Any, context: str) -> dict[str, Any]:
    """Return value as mapping and fail fast for invalid shapes."""

    if isinstance(value, dict):
        return value
    raise ValueError(f"Expected mapping for {context}, got {type(value).__name__}.")


def _as_list_value(value: Any, context: str) -> list[Any]:
    """Return value as list and fail fast for invalid shapes."""

    if isinstance(value, list):
        return value
    raise ValueError(f"Expected list for {context}, got {type(value).__name__}.")


def _is_localized_mapping(value: Any) -> bool:
    """Return whether value is a localized mapping of language codes to strings."""

    if not isinstance(value, dict) or not value:
        return False
    if not all(isinstance(lang, str) for lang in value):
        return False
    if not all(isinstance(text, str) for text in value.values()):
        return False
    return True


def _validate_localized_mapping(value: Any, *, context: str) -> None:
    """Validate a localized mapping and require at least one supported language."""

    if not _is_localized_mapping(value):
        raise LayoutValidationError(f"{context} must be a localized mapping of strings.")
    if "de" not in value and "en" not in value:
        raise LayoutValidationError(f"{context} must contain at least 'de' or 'en'.")


def _validate_string_field(item: dict[str, Any], field: str, *, context: str) -> None:
    """Validate that one mapping field exists and contains a non-empty string."""

    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise LayoutValidationError(f"{context} requires a non-empty string field '{field}'.")


def _validate_text_or_number_field(item: dict[str, Any], field: str, *, context: str) -> None:
    """Validate that one mapping field exists and contains non-empty text or a number."""

    value = item.get(field)
    if isinstance(value, str) and value.strip():
        return
    if isinstance(value, int | float):
        return
    raise LayoutValidationError(
        f"{context} requires a non-empty string or numeric field '{field}'."
    )


def _as_string_list(value: Any, *, context: str) -> list[str] | None:
    """Parse optional list[str] values used in item selection."""

    if value is None:
        return None
    if not isinstance(value, list):
        raise LayoutValidationError(f"{context} must be a list of strings.")
    parsed: list[str] = []
    for entry in value:
        if not isinstance(entry, str) or not entry.strip():
            raise LayoutValidationError(f"{context} must contain non-empty strings only.")
        parsed.append(entry)
    return parsed


# ============================================================================
# Generic YAML loader
# ============================================================================

def _load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file and return its top-level mapping."""

    file_path = Path(path)
    with file_path.open(encoding="utf-8") as file:
        loaded = yaml.safe_load(file)
    return _as_mapping(loaded if loaded is not None else {}, file_path)


def _load_content_parts(
    data_dir: str | Path = "data",
    *,
    layout_filename: str = _DEFAULT_LAYOUT_FILENAME,
) -> dict[str, Any]:
    """Load and merge all top-level content blocks from YAML files."""

    base_dir = Path(data_dir)
    if not base_dir.is_dir():
        raise FileNotFoundError(f"Data directory not found: {base_dir}")

    merged: dict[str, Any] = {}
    yaml_files = sorted(base_dir.glob("*.yaml"))
    if not yaml_files:
        raise FileNotFoundError(f"No YAML files found in data directory: {base_dir}")

    for path in yaml_files:
        if path.name == layout_filename:
            continue
        loaded = _load_yaml(path)
        for key, value in loaded.items():
            if key in merged:
                raise ValueError(f"Duplicate top-level key '{key}' found in '{path}'.")
            merged[key] = value

    return merged


def _is_block_mapping(value: Any) -> bool:
    """Return whether a mapping follows the explicit block shape."""

    return isinstance(value, dict) and isinstance(value.get("kind"), str)


def _parse_block(block_id: str, payload: dict[str, Any]) -> Block:
    """Parse an explicit block definition."""

    unknown_keys = sorted(set(payload.keys()) - _ALLOWED_BLOCK_KEYS)
    if unknown_keys:
        keys = ", ".join(unknown_keys)
        raise ValueError(f"Block '{block_id}' has unsupported keys: {keys}.")

    kind = payload.get("kind")
    if not isinstance(kind, str) or not kind.strip():
        raise ValueError(f"Block '{block_id}' is missing a valid kind.")

    title = payload.get("title")
    if title is not None and not isinstance(title, dict):
        raise ValueError(f"Block '{block_id}' has invalid title mapping.")
    if title is not None:
        _validate_localized_mapping(title, context=f"Block '{block_id}' title")

    items = payload.get("items")
    if items is not None and not isinstance(items, list):
        raise ValueError(f"Block '{block_id}' has invalid items list.")

    text = payload.get("text")
    if text is not None and not isinstance(text, dict):
        raise ValueError(f"Block '{block_id}' has invalid text mapping.")
    if text is not None:
        _validate_localized_mapping(text, context=f"Block '{block_id}' text")

    source = payload.get("source")
    if source is not None and not isinstance(source, dict):
        raise ValueError(f"Block '{block_id}' has invalid source mapping.")

    options = payload.get("options") or {}
    if not isinstance(options, dict):
        raise ValueError(f"Block '{block_id}' has invalid options mapping.")

    data = payload.get("data") or {}
    if not isinstance(data, dict):
        raise ValueError(f"Block '{block_id}' has invalid data mapping.")

    return Block(
        id=block_id,
        kind=kind,
        title=title,
        items=items,
        text=text,
        source=source,
        options=options,
        data=data,
    )


def _validate_block(block: Block) -> None:
    """Validate one normalized block."""

    if block.kind == "profile":
        if not block.data:
            raise LayoutValidationError(f"Block '{block.id}' must define profile data.")
        name = block.data.get("name")
        address = block.data.get("address")
        if not isinstance(name, dict):
            raise LayoutValidationError(f"Block '{block.id}' profile data must include a name mapping.")
        if not isinstance(address, dict):
            raise LayoutValidationError(f"Block '{block.id}' profile data must include an address mapping.")
        _validate_string_field(name, "first", context=f"Block '{block.id}' profile.name")
        _validate_string_field(name, "last", context=f"Block '{block.id}' profile.name")
        _validate_string_field(address, "street", context=f"Block '{block.id}' profile.address")
        _validate_text_or_number_field(address, "postal_code", context=f"Block '{block.id}' profile.address")
        _validate_string_field(address, "city", context=f"Block '{block.id}' profile.address")
        _validate_localized_mapping(address.get("country"), context=f"Block '{block.id}' profile.address.country")
        return

    if block.kind == "quote":
        if not block.text:
            raise LayoutValidationError(f"Block '{block.id}' must define quote text.")
        return

    if block.kind == "timeline":
        if block.items is None:
            raise LayoutValidationError(f"Block '{block.id}' must define timeline items.")
        for index, raw_item in enumerate(block.items, start=1):
            if not isinstance(raw_item, dict):
                raise LayoutValidationError(
                    f"Block '{block.id}' timeline item {index} must be a mapping."
                )
            period = raw_item.get("period")
            if not isinstance(period, dict):
                raise LayoutValidationError(
                    f"Block '{block.id}' timeline item {index} requires a period mapping."
                )
            if "start" not in period or "end" not in period:
                raise LayoutValidationError(
                    f"Block '{block.id}' timeline item {index} period requires start and end."
                )
        return

    if block.kind == "list":
        if block.items is None:
            raise LayoutValidationError(f"Block '{block.id}' must define list items.")
        for index, raw_item in enumerate(block.items, start=1):
            if not isinstance(raw_item, dict):
                raise LayoutValidationError(
                    f"Block '{block.id}' list item {index} must be a mapping."
                )
        return

    if block.kind == "asset":
        if not block.source:
            raise LayoutValidationError(f"Block '{block.id}' must define an asset source.")
        source_type = block.source.get("type")
        if source_type == "website_from_block":
            target = block.source.get("block")
            if not isinstance(target, str) or not target.strip():
                raise LayoutValidationError(
                    f"Block '{block.id}' website_from_block source requires a target block name."
                )
        return

    if block.kind == "text":
        if not block.text:
            raise LayoutValidationError(f"Block '{block.id}' must define text content.")
        return

    raise LayoutValidationError(f"Unsupported block kind '{block.kind}' for block '{block.id}'.")


def load_blocks(data_dir: str | Path = "data") -> dict[str, Block]:
    """Load all explicit content blocks from one or many YAML files."""

    parts = _load_content_parts(data_dir=data_dir)
    blocks: dict[str, Block] = {}

    for key, value in parts.items():
        if not _is_block_mapping(value):
            raise ValueError(
                f"Top-level entry '{key}' must be an explicit block mapping with a kind."
            )
        blocks[key] = _parse_block(key, value)

    if "contact" in blocks and "website_qr" not in blocks:
        blocks["website_qr"] = Block(
            id="website_qr",
            kind="asset",
            source={"type": "website_from_block", "block": "contact"},
            options={"width": 0.35},
        )

    for block in blocks.values():
        _validate_block(block)

    return blocks


def _default_layout_spec() -> LayoutSpec:
    """Return the built-in layout matching the current repository output."""

    return LayoutSpec(
        version=2,
        pages=[
            PageSpec(
                id="page1",
                settings={"sidebar_side": "right"},
                regions={
                    "header": [
                        LayoutPlacement(block="profile", renderer="profile_header"),
                        LayoutPlacement(block="summary_quote", renderer="quote"),
                    ],
                    "body": [
                        LayoutPlacement(block="experience", renderer="timeline"),
                    ],
                    "sidebar": [
                        LayoutPlacement(block="contact", renderer="contact_list"),
                        LayoutPlacement(block="platforms", renderer="comma_list"),
                        LayoutPlacement(block="statistics", renderer="comma_list"),
                        LayoutPlacement(block="soft_skills", renderer="icon_text_list"),
                        LayoutPlacement(block="website_qr", renderer="qr_asset"),
                    ],
                },
            ),
            PageSpec(
                id="page2",
                settings={"sidebar_side": "left"},
                regions={
                    "body": [
                        LayoutPlacement(block="education", renderer="timeline"),
                    ],
                    "sidebar": [
                        LayoutPlacement(block="programming", renderer="rating_list"),
                        LayoutPlacement(block="libraries", renderer="comma_list"),
                        LayoutPlacement(block="awards", renderer="icon_text_list"),
                        LayoutPlacement(block="trainings", renderer="icon_text_list"),
                        LayoutPlacement(block="languages", renderer="language_list"),
                        LayoutPlacement(block="interests", renderer="icon_grid"),
                    ],
                },
            ),
        ],
        settings={},
    )


def _parse_color_overrides(value: Any, *, context: str) -> dict[str, str]:
    """Parse and validate optional named color overrides in HEX format."""

    if not isinstance(value, dict):
        raise LayoutValidationError(f"{context} must be a mapping of color names to HEX values.")

    parsed: dict[str, str] = {}
    for raw_name, raw_hex in value.items():
        if not isinstance(raw_name, str):
            allowed = ", ".join(sorted(_SUPPORTED_COLOR_OVERRIDES))
            raise LayoutValidationError(
                f"{context} has unsupported color '{raw_name}'. Allowed colors: {allowed}."
            )
        if raw_name not in _SUPPORTED_COLOR_OVERRIDES:
            allowed = ", ".join(sorted(_SUPPORTED_COLOR_OVERRIDES))
            raise LayoutValidationError(
                f"{context} has unsupported color '{raw_name}'. Allowed colors: {allowed}."
            )
        if not isinstance(raw_hex, str) or not re.fullmatch(r"[0-9A-Fa-f]{6}", raw_hex.strip()):
            raise LayoutValidationError(
                f"{context}.{raw_name} must be a 6-digit HEX string like '3A4958'."
            )
        parsed[raw_name] = raw_hex.strip().upper()
    return parsed


def _parse_layout_placement(data: dict[str, Any], context: str) -> LayoutPlacement:
    """Parse one block placement within a layout region."""

    block = data.get("block")
    renderer = data.get("renderer")
    if not isinstance(block, str) or not block.strip():
        raise LayoutValidationError(f"{context} is missing a valid block reference.")
    if not isinstance(renderer, str) or not renderer.strip():
        raise LayoutValidationError(f"{context} is missing a valid renderer.")

    item_config = data.get("items") or {}
    if not isinstance(item_config, dict):
        raise LayoutValidationError(f"{context} has invalid item selection config.")

    options = data.get("options") or {}
    if not isinstance(options, dict):
        raise LayoutValidationError(f"{context} has invalid options config.")

    item_include = _as_string_list(item_config.get("include"), context=f"{context} items.include")
    item_exclude = _as_string_list(item_config.get("exclude"), context=f"{context} items.exclude")
    item_order = _as_string_list(item_config.get("order"), context=f"{context} items.order")

    return LayoutPlacement(
        block=block,
        renderer=renderer,
        item_include=item_include,
        item_exclude=item_exclude,
        item_order=item_order,
        options=options,
    )


def _parse_layout_spec(loaded: dict[str, Any]) -> LayoutSpec:
    """Parse a YAML mapping into a validated layout spec."""

    root = loaded.get("layout") if "layout" in loaded else loaded
    if not isinstance(root, dict):
        raise LayoutValidationError("Layout root must be a mapping.")

    version = root.get("version", 2)
    if not isinstance(version, int):
        raise LayoutValidationError("Layout version must be an integer.")

    layout_settings = root.get("settings") or {}
    if not isinstance(layout_settings, dict):
        raise LayoutValidationError("Layout settings must be a mapping.")

    colors = layout_settings.get("colors")
    if colors is not None:
        parsed_settings = dict(layout_settings)
        parsed_settings["colors"] = _parse_color_overrides(
            colors,
            context="Layout settings.colors",
        )
        layout_settings = parsed_settings

    pages_payload = root.get("pages")
    if not isinstance(pages_payload, list) or not pages_payload:
        raise LayoutValidationError("Layout must define at least one page.")

    pages: list[PageSpec] = []
    seen_page_ids: set[str] = set()
    for index, page_payload in enumerate(pages_payload, start=1):
        page = _as_mapping_value(page_payload, f"layout page {index}")
        page_id = page.get("id")
        if not isinstance(page_id, str) or not page_id.strip():
            raise LayoutValidationError(f"Layout page {index} is missing a valid id.")
        if page_id in seen_page_ids:
            raise LayoutValidationError(f"Duplicate layout page id '{page_id}'.")
        seen_page_ids.add(page_id)

        page_settings = page.get("settings") or {}
        if not isinstance(page_settings, dict):
            raise LayoutValidationError(f"Layout page '{page_id}' has invalid settings.")

        regions_payload = page.get("regions") or {}
        if not isinstance(regions_payload, dict):
            raise LayoutValidationError(f"Layout page '{page_id}' has invalid regions.")

        regions: dict[str, list[LayoutPlacement]] = {}
        for region_name, placements_payload in regions_payload.items():
            if region_name not in _SUPPORTED_REGIONS:
                raise LayoutValidationError(f"Unsupported region '{region_name}' on page '{page_id}'.")
            placements = []
            for placement_index, placement_payload in enumerate(
                _as_list_value(placements_payload, f"layout region {region_name}"),
                start=1,
            ):
                placement = _parse_layout_placement(
                    _as_mapping_value(
                        placement_payload,
                        f"layout page '{page_id}' region '{region_name}' item {placement_index}",
                    ),
                    f"layout page '{page_id}' region '{region_name}' item {placement_index}",
                )
                placements.append(placement)
            regions[region_name] = placements

        pages.append(PageSpec(id=page_id, settings=page_settings, regions=regions))

    return LayoutSpec(version=version, pages=pages, settings=layout_settings)


def load_layout_spec(
    data_dir: str | Path = "data",
    *,
    layout_filename: str = _DEFAULT_LAYOUT_FILENAME,
) -> LayoutSpec:
    """Load user-provided layout.yaml or fall back to the built-in default."""

    layout_path = Path(data_dir) / layout_filename
    if not layout_path.is_file():
        return _default_layout_spec()
    return _parse_layout_spec(_load_yaml(layout_path))


def _localized_value(value: Any, lang: str) -> Any:
    """Resolve localized mappings to one language with a stable fallback."""

    if not isinstance(value, Mapping):
        return value
    if lang in value:
        return value[lang]
    if "de" in value:
        return value["de"]
    if "en" in value:
        return value["en"]
    return next(iter(value.values())) if value else None


def _validate_item_selection(placement: LayoutPlacement, items: list[dict[str, Any]]) -> None:
    """Validate optional item-level selection rules for one placement."""

    requested_ids = [
        *list(placement.item_include or []),
        *list(placement.item_exclude or []),
        *list(placement.item_order or []),
    ]
    if not requested_ids:
        return

    known_ids = {str(item.get("id")) for item in items if item.get("id") is not None}
    if placement.item_include and placement.item_exclude:
        overlap = sorted(set(placement.item_include) & set(placement.item_exclude))
        if overlap:
            joined = ", ".join(overlap)
            raise LayoutValidationError(
                f"Placement for block '{placement.block}' has overlapping include/exclude ids: {joined}."
            )
    missing = [item_id for item_id in requested_ids if item_id not in known_ids]
    if missing:
        raise LayoutValidationError(
            f"Placement for block '{placement.block}' references unknown item ids: {', '.join(missing)}."
        )


def _validate_renderer_shape(block: Block, placement: LayoutPlacement) -> None:
    """Validate renderer-specific item requirements."""

    items = block.items or []
    if placement.renderer == "timeline":
        for index, item in enumerate(items, start=1):
            if block.id == "education":
                _validate_string_field(item, "institution", context=f"Block '{block.id}' timeline item {index}")
                degree = item.get("degree")
                details = item.get("details")
                if not _is_localized_mapping(degree):
                    raise LayoutValidationError(
                        f"Block '{block.id}' timeline item {index} requires localized degree mapping."
                    )
                if not isinstance(details, dict) or not details:
                    raise LayoutValidationError(
                        f"Block '{block.id}' timeline item {index} requires localized details lists."
                    )
                for lang, points in details.items():
                    if not isinstance(lang, str):
                        raise LayoutValidationError(
                            f"Block '{block.id}' timeline item {index} details languages must be strings."
                        )
                    if not isinstance(points, list) or not all(isinstance(p, str) for p in points):
                        raise LayoutValidationError(
                            f"Block '{block.id}' timeline item {index} details[{lang}] must be a list of strings."
                        )
            else:
                _validate_string_field(item, "organization", context=f"Block '{block.id}' timeline item {index}")
                title = item.get("title")
                highlights = item.get("highlights")
                if not _is_localized_mapping(title):
                    raise LayoutValidationError(
                        f"Block '{block.id}' timeline item {index} requires localized title mapping."
                    )
                if not isinstance(highlights, dict) or not highlights:
                    raise LayoutValidationError(
                        f"Block '{block.id}' timeline item {index} requires localized highlights lists."
                    )
                for lang, points in highlights.items():
                    if not isinstance(lang, str):
                        raise LayoutValidationError(
                            f"Block '{block.id}' timeline item {index} highlights languages must be strings."
                        )
                    if not isinstance(points, list) or not all(isinstance(p, str) for p in points):
                        raise LayoutValidationError(
                            f"Block '{block.id}' timeline item {index} highlights[{lang}] must be a list of strings."
                        )
        return

    if placement.renderer == "icon_text_list":
        for index, item in enumerate(items, start=1):
            _validate_string_field(item, "icon", context=f"Block '{block.id}' item {index}")
            if "label" not in item and "title" not in item:
                raise LayoutValidationError(
                    f"Block '{block.id}' requires icon and label or title for renderer 'icon_text_list'."
                )
            if "label" in item:
                _validate_localized_mapping(item.get("label"), context=f"Block '{block.id}' item {index} label")
            if "title" in item:
                _validate_localized_mapping(item.get("title"), context=f"Block '{block.id}' item {index} title")
    elif placement.renderer == "rating_list":
        for index, item in enumerate(items, start=1):
            if not {"skill", "icon", "level"}.issubset(item):
                raise LayoutValidationError(
                    f"Block '{block.id}' requires skill, icon, and level for renderer 'rating_list'."
                )
            _validate_string_field(item, "skill", context=f"Block '{block.id}' item {index}")
            _validate_string_field(item, "icon", context=f"Block '{block.id}' item {index}")
            if not isinstance(item.get("level"), int):
                raise LayoutValidationError(
                    f"Block '{block.id}' item {index} level must be an integer for renderer 'rating_list'."
                )
    elif placement.renderer == "language_list":
        for index, item in enumerate(items, start=1):
            if "flag" not in item or "level" not in item:
                raise LayoutValidationError(
                    f"Block '{block.id}' requires flag and level for renderer 'language_list'."
                )
            _validate_string_field(item, "flag", context=f"Block '{block.id}' item {index}")
            _validate_localized_mapping(item.get("level"), context=f"Block '{block.id}' item {index} level")
    elif placement.renderer == "icon_grid":
        for index, item in enumerate(items, start=1):
            if "icon" not in item:
                raise LayoutValidationError(
                    f"Block '{block.id}' requires icon for renderer 'icon_grid'."
                )
            _validate_string_field(item, "icon", context=f"Block '{block.id}' item {index}")
    elif placement.renderer == "contact_list":
        for index, item in enumerate(items, start=1):
            if "type" not in item:
                raise LayoutValidationError(
                    f"Block '{block.id}' requires type for renderer 'contact_list'."
                )
            contact_type = item.get("type")
            if not isinstance(contact_type, str) or contact_type not in _SUPPORTED_CONTACT_TYPES:
                raise LayoutValidationError(
                    f"Block '{block.id}' item {index} has unsupported contact type '{contact_type}'."
                )
            _validate_string_field(item, "icon", context=f"Block '{block.id}' item {index}")
            if contact_type in {"phone", "email"}:
                _validate_string_field(item, "value", context=f"Block '{block.id}' item {index}")
            if contact_type in {"website", "linkedin", "github", "stackoverflow"}:
                _validate_string_field(item, "label", context=f"Block '{block.id}' item {index}")
                _validate_string_field(item, "url", context=f"Block '{block.id}' item {index}")
    elif placement.renderer == "comma_list":
        for index, item in enumerate(items, start=1):
            label = item.get("label")
            if isinstance(label, str) and label.strip():
                continue
            if _is_localized_mapping(label):
                continue
            raise LayoutValidationError(
                f"Block '{block.id}' item {index} requires a string or localized label for renderer 'comma_list'."
            )


def _validate_layout(blocks: dict[str, Block], layout: LayoutSpec) -> None:
    """Validate block references and renderer compatibility within the layout."""

    for page in layout.pages:
        sidebar_side = page.settings.get("sidebar_side")
        if sidebar_side is not None and sidebar_side not in {"left", "right"}:
            raise LayoutValidationError(
                f"Page '{page.id}' has invalid sidebar_side '{sidebar_side}'."
            )
        for region_name, placements in page.regions.items():
            if region_name not in _SUPPORTED_REGIONS:
                raise LayoutValidationError(f"Unsupported region '{region_name}'.")
            for placement in placements:
                block = blocks.get(placement.block)
                if block is None:
                    raise LayoutValidationError(
                        f"Layout references unknown block '{placement.block}'."
                    )
                allowed_kinds = _RENDERER_COMPATIBILITY.get(placement.renderer)
                if allowed_kinds is None:
                    raise LayoutValidationError(
                        f"Layout uses unsupported renderer '{placement.renderer}'."
                    )
                if block.kind not in allowed_kinds:
                    raise LayoutValidationError(
                        f"Block '{block.id}' of kind '{block.kind}' cannot use renderer '{placement.renderer}'."
                    )
                _validate_item_selection(placement, block.items or [])
                _validate_renderer_shape(block, placement)


def _select_items(block: Block, placement: LayoutPlacement) -> list[dict[str, Any]] | None:
    """Apply include, exclude, and order filters to block items."""

    if block.items is None:
        return None

    items = list(block.items)
    if placement.item_include:
        include = set(placement.item_include)
        items = [item for item in items if item.get("id") in include]
    if placement.item_exclude:
        exclude = set(placement.item_exclude)
        items = [item for item in items if item.get("id") not in exclude]
    if placement.item_order:
        order = {item_id: index for index, item_id in enumerate(placement.item_order)}
        tail_offset = len(order)
        items = sorted(
            items,
            key=lambda item: (order.get(item.get("id"), tail_offset), block.items.index(item)),
        )
    return items


def _prepare_unit_data(block: Block, placement: LayoutPlacement, lang: str) -> dict[str, Any]:
    """Prepare a renderer-ready payload for one normalized block placement."""

    data = dict(block.data)
    selected_items = _select_items(block, placement)
    if selected_items is not None:
        data["items"] = selected_items
    if block.text is not None:
        data["text"] = _localized_value(block.text, lang)
    if block.source is not None:
        data["source"] = block.source
    if block.options:
        data["options"] = dict(block.options)
    if placement.options:
        data["placement_options"] = dict(placement.options)
    return data


def load_render_document(
    data_dir: str | Path = "data",
    *,
    lang: str = "de",
) -> RenderDocument:
    """Load the normalized render document from blocks and layout."""

    blocks = load_blocks(data_dir=data_dir)
    layout = load_layout_spec(data_dir=data_dir)
    _validate_layout(blocks, layout)

    pages: list[RenderPage] = []
    profile_block = blocks.get("profile")
    if profile_block is None:
        raise LayoutValidationError("Missing required profile block.")

    for page in layout.pages:
        regions: dict[str, list[RenderUnit]] = {}
        for region_name, placements in page.regions.items():
            units: list[RenderUnit] = []
            for placement in placements:
                block = blocks[placement.block]
                units.append(
                    RenderUnit(
                        block_id=block.id,
                        renderer=placement.renderer,
                        title=_localized_value(block.title, lang) if block.title else None,
                        data=_prepare_unit_data(block, placement, lang),
                    )
                )
            regions[region_name] = units
        pages.append(RenderPage(id=page.id, settings=dict(page.settings), regions=regions))

    return RenderDocument(
        lang=lang,
        profile=dict(profile_block.data),
        pages=pages,
        settings=dict(layout.settings),
    )
__all__ = [
    "Block",
    "LayoutPlacement",
    "LayoutSpec",
    "LayoutValidationError",
    "PageSpec",
    "RenderDocument",
    "RenderPage",
    "RenderUnit",
    "load_blocks",
    "load_layout_spec",
    "load_render_document",
]
