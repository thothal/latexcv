# CV Specification

## Goal

This schema separates content storage from document composition.

- Content may live in one YAML file or many YAML files.
- Reusable content blocks have stable IDs.
- A layout file decides where blocks are placed and how they are rendered.
- Python validates the document before Jinja renders LaTeX.

This repository uses this schema as the supported content format.

## Core Concepts

### Block

A reusable content unit keyed by a globally unique ID.

Required properties:

- `kind`

Optional properties:

- `title`
- `items`
- `text`
- `source`
- `options`
- `data`

Supported block kinds:

- `profile`
- `quote`
- `timeline`
- `list`
- `asset`
- `text`

### Layout

The layout file decides:

- page count
- page settings
- region placement
- ordering
- renderer choice

Supported regions:

- `header`
- `body`
- `sidebar`

### Renderer

Renderers are implemented in Python and selected from YAML.

Supported renderers:

- `profile_header`
- `quote`
- `timeline`
- `contact_list`
- `icon_text_list`
- `comma_list`
- `rating_list`
- `language_list`
- `icon_grid`
- `qr_asset`
- `plain_text`

## Content Schema

### Generic Block Envelope

```yaml
experience:
  kind: timeline
  title:
    de: Berufserfahrung
    en: Work Experience
  items:
    - period:
        start: 2025-06
        end: present
      organization: Example Analytics GmbH
      title:
        de: Senior Data Analyst
        en: Senior Data Analyst
      highlights:
        de:
          - Leitung standortuebergreifender Analytics-Teams
        en:
          - Lead cross-location analytics teams
```

### Quote Block

```yaml
summary_quote:
  kind: quote
  text:
    de: Kurzprofil als Platzhaltertext fuer ein Beispiel-CV.
    en: Placeholder summary text for a sample CV.
```

### Asset Block

```yaml
website_qr:
  kind: asset
  source:
    type: website_from_block
    block: contact
  options:
    width: 0.35
```

### Optional Item IDs

Items only need IDs when the layout references them individually.

```yaml
trainings:
  kind: list
  title:
    de: Weiterbildungen
    en: Trainings
  items:
    - id: train_the_trainer
      icon: chalkboard-teacher
      label:
        de: Train the Trainer
        en: Train the Trainer
```

## Layout Schema

```yaml
layout:
  version: 2
  settings:
    colors:
      panel_background: "3A4958"
      accent: "F9A620"
  pages:
    - id: page1
      settings:
        sidebar_side: right
      regions:
        header:
          - block: profile
            renderer: profile_header
          - block: summary_quote
            renderer: quote
        body:
          - block: experience
            renderer: timeline
        sidebar:
          - block: contact
            renderer: contact_list
          - block: soft_skills
            renderer: icon_text_list
          - block: website_qr
            renderer: qr_asset
```

Optional item-level selection:

```yaml
- block: trainings
  renderer: icon_text_list
  items:
    include:
      - train_the_trainer
```

Concrete example from the fake example layout:

```yaml
- block: trainings
  renderer: icon_text_list
  items:
    include:
      - six_sigma_green_belt
      - train_the_trainer
    order:
      - six_sigma_green_belt
      - train_the_trainer
```

Supported item-level operations:

- `include`
- `exclude`
- `order`

Optional global layout settings:

- `colors`: override built-in LaTeX class colors.

Supported color keys:

- `panel_background`
- `panel_foreground`
- `footer_background`
- `footer_foreground`
- `page_background`
- `page_foreground`
- `section_marker`
- `timeline_meta`
- `accent`

Color values must be quoted 6-digit HEX strings (for example `"3A4958"`). If omitted, class defaults are used.

## Validation Rules

- Block IDs are globally unique.
- Top-level content entries must be explicit blocks with a `kind`.
- Unknown layout block references fail validation.
- Item-level references require matching item IDs.
- Item-level `include`, `exclude`, and `order` values must be lists of non-empty strings.
- Renderer compatibility is validated before Jinja runs.
- Localized values must support the requested language or a fallback.
- Asset sources must resolve deterministically.

Additional strict checks in this repository:

- Blocks reject unknown top-level keys.
- Profile blocks require `name.first` and `name.last`; address fields are optional.
- Timeline and list blocks validate item mappings and required period fields.
- Renderer-specific item fields are validated early (e.g., `rating_list` requires `skill`, `icon`, `level`).

Contact renderer minimum:

- `contact_list` requires only `type` and `icon` per item.
- Type-specific fields are optional, but when link fields are provided they must include both `label` and `url`.

Compatibility examples:

- `timeline` accepts `timeline` blocks only.
- `quote` accepts `quote` blocks only.
- `qr_asset` accepts `asset` blocks only.
- `comma_list` accepts `list` blocks with labels or strings.
- `icon_text_list` accepts `list` blocks with `icon` and `label`.
- `rating_list` accepts `list` blocks with `skill`, `icon`, and `level`.

## Repository Mapping

The current repository maps naturally into these blocks:

- `profile`
- `summary_quote`
- `contact`
- `experience`
- `education`
- `platforms`
- `statistics`
- `soft_skills`
- `programming`
- `libraries`
- `awards`
- `trainings`
- `languages`
- `interests`
- `website_qr`

Titles belong directly to the blocks themselves.

## Pipeline

1. Discover all YAML files under the data directory.
2. Exclude `layout.yaml` from content loading.
3. Merge top-level content keys and fail on duplicates.
4. Require each top-level entry to be an explicit block with a `kind`.
5. Validate each block by kind.
6. Load and validate `layout.yaml`.
7. Build a normalized render document.
8. Render the document to LaTeX through Jinja.