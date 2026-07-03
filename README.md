# latexcv

Render and compile CVs from YAML data using Jinja2 templates and LaTeX.

This repository is intentionally tool-focused and contains only sample data.

## Overview

- Python package and CLI: [latexcv](latexcv)
- LaTeX/Jinja templates: [layout](layout)
- Sample example profile: [examples/sample-cv/data](examples/sample-cv/data)
- Optional R wrapper: [wrappers/r/render.R](wrappers/r/render.R)

## Requirements

- Python 3.10+
- Conda (Miniconda/Anaconda)
- A LaTeX distribution with `latexmk` available in PATH

## Quick Start

1. Clone the repository.
2. Verify LaTeX tooling:

```powershell
latexmk -v
```

3. Create and activate the conda environment:

```powershell
conda env create -f environment.yml
conda activate cv-render
```

4. Install in editable mode:

```powershell
python -m pip install -e .
```

5. Render the sample profile:

```powershell
cv-render examples/sample-cv/data --output-dir examples/sample-cv/output --lang en
cv-render examples/sample-cv/data --output-dir examples/sample-cv/output --lang de
```

## CLI Usage

The CLI expects:

- required positional `data_dir`
- optional `--output-dir` (default: current directory)
- optional `--lang` (default: `en`)

Examples:

```powershell
cv-render examples/sample-cv/data
cv-render examples/sample-cv/data --output-dir examples/sample-cv/output --lang de --tex-only
```

## Document Model

The renderer uses a block-and-layout content model:

- top-level reusable blocks with stable IDs
- `layout.yaml` controls page placement and renderer kind
- Python validates schema and renderer compatibility before Jinja rendering

See [docs/cv-spec.md](docs/cv-spec.md) for details.

## Troubleshooting

- If `cv-render` is not found:

```powershell
python -m latexcv.cli examples/sample-cv/data --output-dir examples/sample-cv/output --lang en
```

- If PDF compilation fails, verify `latexmk`:

```powershell
latexmk -v
```

- If QR code is missing, ensure contact data includes a `website` URL and the layout includes a `qr_asset` unit.