# latexcv

Render and compile CVs from YAML data using Jinja2 templates and LaTeX.

This repository is intentionally tool-focused and contains only sample data.

## Overview

- Python package and CLI: [latexcv](latexcv)
- LaTeX/Jinja templates: [layout](layout)
- Full showcase profile: [examples/full-showcase/data](examples/full-showcase/data)
- Optional R wrapper: [wrappers/r/render.R](wrappers/r/render.R)

## Requirements

- Python 3.10+
- Conda (Miniconda/Anaconda)
- A LaTeX distribution with `latexmk` available in PATH

## Environment Strategy

Use two conda environments:

- Runtime: `cv-render` (used by consumer repositories/scripts)
- Development: `cv-render-dev` (used while developing `latexcv` itself)

Keep `base` clean and do not install this project there.

## Quick Start

1. Clone the repository.
2. Verify LaTeX tooling:

```powershell
latexmk -v
```

3. Create and activate the runtime environment:

```powershell
conda env create -f environment.yml
conda activate cv-render
```

4. Install package in the runtime environment:

```powershell
python -m pip install .
```

5. Render the sample profile:

```powershell
cvrender examples/full-showcase/data --output-dir examples/full-showcase/output --lang en
cvrender examples/full-showcase/data --output-dir examples/full-showcase/output --lang de
```

## Development Setup

1. Create and activate the development environment:

```powershell
conda env create -f environment.dev.yml
conda activate cv-render-dev
```

2. Install in editable mode:

```powershell
python -m pip install -e .
```

3. Run quality checks:

```powershell
ruff check .
pytest -q
```

4. Render additional layout examples:

```powershell
cvrender examples/compact-one-page/data --output-dir examples/compact-one-page/output --lang en --tex-only
cvrender examples/skills-focused/data --output-dir examples/skills-focused/output --lang en --tex-only
```

## CLI Usage

The CLI expects:

- required positional `data_dir`
- optional `--output-dir` (default: current directory)
- optional `-o, --output FILE` (explicit output file path/name)
- optional `-l, --lang` (default: `en`)
- optional `-t, --tex-only`
- optional `-C, --[no-]cleanup`
- optional `-F, --[no-]format-output`

Examples:

```powershell
cvrender examples/full-showcase/data
cvrender examples/full-showcase/data --output-dir examples/full-showcase/output --lang de --tex-only
cvrender examples/full-showcase/data -o examples/full-showcase/output/my-cv.pdf --lang en
cvrender examples/full-showcase/data -o examples/full-showcase/output/my-cv.tex --lang en --tex-only
cvrender examples/full-showcase/data -l de -t -o examples/full-showcase/output/short-opts.tex
```

## Document Model

The renderer uses a block-and-layout content model:

- top-level reusable blocks with stable IDs
- `layout.yaml` controls page placement and renderer kind
- Python validates schema and renderer compatibility before Jinja rendering

See [docs/cv-spec.md](docs/cv-spec.md) for details.
For implementation and extension guidance, see [docs/developer-validation-renderers-tests.md](docs/developer-validation-renderers-tests.md).

## Troubleshooting

- If `cvrender` is not found:

```powershell
python -m latexcv.cli examples/full-showcase/data --output-dir examples/full-showcase/output --lang en
```

- If PDF compilation fails, verify `latexmk`:

```powershell
latexmk -v
```

- If QR code is missing, ensure contact data includes a `website` URL and the layout includes a `qr_asset` unit.