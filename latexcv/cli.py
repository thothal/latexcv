"""Command-line interface for rendering and compiling CV documents."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
	from .compiler import compile_tex_file
	from .render import render_tex_file
except ImportError:  # pragma: no cover - supports direct script execution
	from latexcv.compiler import compile_tex_file
	from latexcv.render import render_tex_file

def build_parser() -> argparse.ArgumentParser:
	"""Create and return the CLI argument parser."""

	parser = argparse.ArgumentParser(
		prog="cvrender",
		description="Render CV templates to TeX or compile all the way to PDF.",
	)

	parser.add_argument(
		"data_dir",
		help="Path to CV YAML data directory (mandatory).",
	)
	parser.add_argument(
		"--output-dir",
		default=".",
		help="Path to output directory (default: current directory).",
	)
	parser.add_argument(
		"-o",
		"--output",
		metavar="FILE",
		help="Write output to FILE (.pdf by default, .tex with --tex-only).",
	)
	parser.add_argument(
		"-l",
		"--lang",
		default="en",
		help="Language code used for rendering (default: en).",
	)
	parser.add_argument(
		"-t",
		"--tex-only",
		action="store_true",
		help="Only render TeX and skip PDF compilation.",
	)
	parser.add_argument(
		"-C",
		"--cleanup",
		action=argparse.BooleanOptionalAction,
		default=True,
		help="Clean auxiliary compile files after PDF generation (default: enabled).",
	)
	parser.add_argument(
		"-F",
		"--format-output",
		action=argparse.BooleanOptionalAction,
		default=False,
		help="Run latexindent formatting on rendered TeX before compile (default: disabled).",
	)

	return parser


def main(argv: list[str] | None = None) -> int:
	"""Run CLI workflow and return process exit code."""

	parser = build_parser()
	args = parser.parse_args(argv)

	try:
		output_dir = args.output_dir
		output_basename = None
		if args.output:
			requested_output = Path(args.output)
			expected_suffix = ".tex" if args.tex_only else ".pdf"
			if requested_output.suffix and requested_output.suffix.lower() != expected_suffix:
				raise ValueError(
					f"--output must use '{expected_suffix}' extension"
				)
			if not requested_output.suffix:
				requested_output = requested_output.with_suffix(expected_suffix)
			output_dir = str(requested_output.parent) if str(requested_output.parent) else "."
			output_basename = requested_output.stem

		tex_path = render_tex_file(
			data_dir=args.data_dir,
			output_dir=output_dir,
			lang=args.lang,
			output_basename=output_basename,
			format_output=args.format_output,
		)

		if args.tex_only:
			print(tex_path)
			return 0

		pdf_path = compile_tex_file(
			tex_file=tex_path,
			output_dir=output_dir,
			cleanup=args.cleanup,
		)
		print(pdf_path)
		return 0
	except Exception as exc:  # pragma: no cover - CLI error path
		print(f"Error: {exc}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
