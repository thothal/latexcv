"""Render CV templates to LaTeX output."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any
import warnings

from jinja2 import Environment, FileSystemLoader, PackageLoader, StrictUndefined
import qrcode

from .filters import register_filters
from .loader import load_blocks, load_render_document


_DEFAULT_LANG = "de"
_DEFAULT_DATA_DIR = "data"
_DEFAULT_LAYOUT_DIR: str | Path | None = None
_DEFAULT_OUTPUT_DIR = "output"
_DEFAULT_TEMPLATE = "cv.tex.j2"


def _resolve_default_layout_dir() -> Path | None:
    """Return repository layout dir when present, else use packaged templates."""

    package_root = Path(__file__).resolve().parent
    repo_layout_dir = package_root.parent / "layout"
    if repo_layout_dir.is_dir():
        return repo_layout_dir
    packaged_layout_dir = package_root / "layout"
    if packaged_layout_dir.is_dir():
        return packaged_layout_dir
    return None


def _babel_language(lang: str) -> str:
    """Map language code to babel package language option."""

    return "ngerman" if lang == "de" else "english"


# ============================================================================
# Context
# ============================================================================

def build_context(
    data_dir: str | Path = _DEFAULT_DATA_DIR,
    lang: str = _DEFAULT_LANG,
    qr_code_path: str | None = None,
) -> dict[str, Any]:
    """Load CV data and build the Jinja rendering context."""

    document = load_render_document(data_dir=data_dir, lang=lang)
    blocks = load_blocks(data_dir=data_dir)
    contact_block = blocks.get("contact")

    return {
        "document": document,
        "contact": list(contact_block.items) if contact_block is not None and contact_block.items is not None else [],
        "lang": lang,
        "babel_language": _babel_language(lang),
        "color_overrides": dict(document.settings.get("colors", {})),
        "qr_code_path": qr_code_path,
    }


def _website_url(contact: Any) -> str | None:
    """Extract website URL from contact entries if present."""

    if not isinstance(contact, list):
        return None

    for item in contact:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "website":
            continue
        url = item.get("url")
        if isinstance(url, str) and url.strip():
            return url.strip()
    return None


def _cached_qr_code_path(output_dir: str | Path, content: str) -> Path:
    """Return deterministic cache path for QR code content."""

    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    cache_dir = Path(output_dir) / ".cache" / "qr"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"qr_{digest}.png"


def _resolve_qr_code_path(
    context: dict[str, Any],
    *,
    output_dir: str | Path,
    qr_requested: bool,
) -> str | None:
    """Create or reuse QR code asset and return TeX-relative path."""

    if not qr_requested:
        return None

    url = _website_url(context.get("contact"))
    if not url:
        warnings.warn(
            "QR code requested but no website URL found in contact entries; skipping QR code.",
            stacklevel=2,
        )
        return None

    qr_path = _cached_qr_code_path(output_dir, url)
    if not qr_path.exists():
        image = qrcode.make(url)
        image.save(qr_path)

    output_path = Path(output_dir)
    return qr_path.relative_to(output_path).as_posix()


def _layout_requests_qr(document: Any) -> bool:
    """Return whether any layout unit uses the qr_asset renderer."""

    pages = getattr(document, "pages", None)
    if not isinstance(pages, list):
        return False

    for page in pages:
        regions = getattr(page, "regions", None)
        if not isinstance(regions, dict):
            continue
        for units in regions.values():
            if not isinstance(units, list):
                continue
            for unit in units:
                if getattr(unit, "renderer", None) == "qr_asset":
                    return True
    return False


# ============================================================================
# Environment
# ============================================================================

def create_environment(
    layout_dir: str | Path = _DEFAULT_LAYOUT_DIR,
    lang: str = _DEFAULT_LANG,
) -> Environment:
    """Create a configured Jinja environment with project filters."""

    effective_layout_dir = _resolve_default_layout_dir() if layout_dir is None else Path(layout_dir)
    if effective_layout_dir is None:
        loader = PackageLoader("latexcv", "layout")
    else:
        loader = FileSystemLoader(str(effective_layout_dir))

    env = Environment(
        loader=loader,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    register_filters(env, lang=lang)
    return env


# ============================================================================
# Render TEX
# ============================================================================

def render_tex(
    data_dir: str | Path = _DEFAULT_DATA_DIR,
    layout_dir: str | Path | None = _DEFAULT_LAYOUT_DIR,
    output_dir: str | Path = _DEFAULT_OUTPUT_DIR,
    lang: str = _DEFAULT_LANG,
    template_name: str = _DEFAULT_TEMPLATE,
) -> str:
    """Render and return the LaTeX string for a template."""

    context = build_context(data_dir=data_dir, lang=lang)
    qr_requested = _layout_requests_qr(context.get("document"))
    context["qr_code_path"] = _resolve_qr_code_path(
        context,
        output_dir=output_dir,
        qr_requested=qr_requested,
    )
    env = create_environment(layout_dir=layout_dir, lang=lang)
    template = env.get_template(template_name)
    return template.render(**context)


# ============================================================================
# Format TEX file
# ============================================================================

def format_tex_file(
    tex_file: str | Path,
    formatter_command: str = "latexindent",
) -> str:
    """Format a LaTeX file without creating latexindent backup files."""

    file_path = Path(tex_file)
    temp_path: Path | None = None

    with tempfile.NamedTemporaryFile(
        suffix=file_path.suffix or ".tex",
        dir=file_path.parent,
        delete=False,
    ) as temp_file:
        temp_path = Path(temp_file.name)

    result = subprocess.run(
        [
            formatter_command,
            "-s",
            "-g",
            os.devnull,
            f"-o={temp_path}",
            str(file_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
        details = (result.stderr or result.stdout).strip()
        raise RuntimeError(
            f"LaTeX formatting failed for '{file_path}': {details}"
        )

    if temp_path is not None:
        temp_path.replace(file_path)

    return str(file_path)


# ============================================================================
# Write TEX file
# ============================================================================

def render_tex_file(
    data_dir: str | Path = _DEFAULT_DATA_DIR,
    layout_dir: str | Path | None = _DEFAULT_LAYOUT_DIR,
    output_dir: str | Path = _DEFAULT_OUTPUT_DIR,
    lang: str = _DEFAULT_LANG,
    output_basename: str | None = None,
    template_name: str = _DEFAULT_TEMPLATE,
    format_output: bool = True,
    formatter_command: str = "latexindent",
) -> str:
    """Render LaTeX and write it to an output .tex file."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    tex = render_tex(
        data_dir=data_dir,
        layout_dir=layout_dir,
        output_dir=output_path,
        lang=lang,
        template_name=template_name,
    )

    target_stem = output_basename or f"cv_{lang}"
    rendered_file = output_path / f"{target_stem}.tex"
    rendered_file.write_text(tex, encoding="utf-8")

    if format_output:
        format_tex_file(rendered_file, formatter_command=formatter_command)

    return str(rendered_file)


__all__ = [
    "build_context",
    "create_environment",
    "render_tex",
    "format_tex_file",
    "render_tex_file",
]
