# Developer Guide: Validation, Renderers, and Tests

This guide explains how data validation works, how renderer integration works, and how to extend both safely.

## Scope and Intent

Use this guide when you need to:

- understand why a block/layout fails validation
- relax or tighten schema requirements
- add a new renderer end-to-end
- update tests after schema or rendering changes

For schema examples, keep using docs/cv-spec.md.

## Validation Architecture

Validation happens in latexcv/loader.py during document load.

Main flow:

1. load_blocks:
   - reads all YAML except layout.yaml
   - merges top-level block IDs
   - parses each block with _parse_block
   - validates each block with _validate_block
2. load_layout_spec:
   - loads layout.yaml (or default layout)
   - validates shape via _parse_layout_spec
3. _validate_layout:
   - checks block references exist
   - checks renderer-kind compatibility
   - validates item selection rules and renderer-specific item fields
4. load_render_document:
   - assembles validated, normalized RenderDocument for Jinja rendering

Important validation entry points:

- _validate_block
- _validate_layout
- _validate_renderer_shape
- _validate_item_selection

## Current Minimum Required Fields

### Profile block

Required:

- data.name.first
- data.name.last

Optional:

- data.address
- data.address.street
- data.address.postal_code
- data.address.city
- data.address.country

Behavior note:

- optional address fields are validated only when provided
- rendering uses fallback-safe filters, so missing address fields do not crash templates

### Contact list (renderer contact_list)

Per item required:

- type
- icon

Optional by contact type:

- phone/email: value optional
- website/linkedin/github/stackoverflow: label+url optional as a pair

Consistency rule:

- if label is present for a link contact, url must also be present (and vice versa)

## How To Tweak Validation Rules

### Relax requirements

1. adjust block-level requirements in _validate_block
2. adjust renderer-specific item requirements in _validate_renderer_shape
3. make sure templates and filters can handle missing values
4. update tests and docs

### Tighten requirements

1. add explicit checks and clear LayoutValidationError messages
2. keep checks close to existing block/renderer sections
3. add or update tests that assert failure behavior
4. document the new required fields in docs/cv-spec.md and this guide

## Renderer System: Existing Renderers

Compatibility is defined in _RENDERER_COMPATIBILITY in latexcv/loader.py.

Current renderers:

- profile_header
- quote
- timeline
- contact_list
- icon_text_list
- comma_list
- rating_list
- language_list
- icon_grid
- qr_asset
- plain_text

Template dispatch is implemented in layout/macros.tex.j2, primarily inside render_header_unit, render_body_unit, and render_sidebar_unit.

## Adding a New Renderer (Developer Workflow)

1. Add compatibility mapping
   - update _RENDERER_COMPATIBILITY in latexcv/loader.py
   - map renderer name to allowed block kind(s)

2. Add validation rules
   - extend _validate_renderer_shape with item/data requirements
   - keep messages explicit and actionable

3. Add template rendering branch
   - implement renderer output in layout/macros.tex.j2
   - keep output stable and deterministic for testing

4. Use in layout
   - reference renderer in data/layout.yaml
   - ensure block kind matches compatibility mapping

5. Add tests
   - one positive test that renders successfully
   - one negative test for invalid input if renderer has strict fields

6. Update docs
   - add renderer to docs/cv-spec.md and this guide

## Coupling Renderers with Validation

Rule of thumb:

- validation should reject malformed data early
- templates should still be resilient for optional fields

Practical split:

- loader.py owns data contract and compatibility enforcement
- macros.tex.j2 owns visual output structure
- filters.py provides safe data access and formatting helpers

If you make a field optional in validation, make sure template/filter access no longer assumes the field always exists.

## Test Suite Guide

Current tests are in tests/:

- tests/test_cli.py: CLI argument behavior and control flow
- tests/test_render.py: rendering structure and schema flexibility checks

Run locally:

- ruff check .
- pytest -q

### When changing validation

Add/update tests for:

- successful loading/rendering with allowed optional omissions
- failing loads with clear LayoutValidationError for invalid shapes

### When changing renderer output

Add/update tests for:

- expected output structure (for example line-break behavior)
- smoke rendering from example data

### Keep tests robust

Prefer structure assertions over brittle full-file snapshots unless you intentionally manage golden files.

## Documentation Sync Checklist

When making schema/renderer changes, update all of:

1. docs/cv-spec.md
2. docs/developer-validation-renderers-tests.md
3. README.md section links if navigation changed
4. tests that encode expected behavior

This prevents drift between implementation, examples, and onboarding docs.
