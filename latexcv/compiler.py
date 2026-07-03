"""Compile rendered LaTeX files to PDF."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


_PACKAGE_ROOT = Path(__file__).resolve().parent
_DEFAULT_OUTPUT_DIR = "output"
_DEFAULT_COMPILER = "latexmk"


def _resolve_default_classes_dir() -> Path:
	"""Return repository classes dir when present, else packaged classes dir."""

	repo_classes_dir = _PACKAGE_ROOT.parent / "layout" / "classes"
	if repo_classes_dir.is_dir():
		return repo_classes_dir
	return _PACKAGE_ROOT / "layout" / "classes"


_DEFAULT_CLASSES_DIR = _resolve_default_classes_dir()


def _texinputs(classes_dir: Path) -> str:
	"""Build TEXINPUTS value that preserves default search paths."""

	existing = os.environ.get("TEXINPUTS", "")
	prefix = f"{classes_dir.resolve().as_posix()}//{os.pathsep}"
	return f"{prefix}{existing}" if existing else prefix


def compile_tex_file(
	tex_file: str | Path,
	output_dir: str | Path | None = None,
	classes_dir: str | Path = _DEFAULT_CLASSES_DIR,
	compiler_command: str = _DEFAULT_COMPILER,
	cleanup: bool = True,
) -> str:
	"""Compile a LaTeX file to PDF using latexmk."""

	cwd = Path.cwd()
	tex_path = Path(tex_file)
	if not tex_path.is_absolute():
		tex_path = (cwd / tex_path).resolve()

	output_path = Path(output_dir) if output_dir is not None else tex_path.parent
	if not output_path.is_absolute():
		output_path = (cwd / output_path).resolve()
	output_path.mkdir(parents=True, exist_ok=True)

	class_path = Path(classes_dir)
	if not class_path.is_absolute():
		class_path = (cwd / class_path).resolve()

	env = os.environ.copy()
	env["TEXINPUTS"] = _texinputs(class_path)

	command = [
		compiler_command,
		"-pdf",
		"-interaction=nonstopmode",
		"-file-line-error",
		"-outdir=" + str(output_path),
		str(tex_path),
	]

	result = subprocess.run(
		command,
		cwd=None,
		env=env,
		check=False,
		capture_output=True,
		text=True,
	)

	if result.returncode != 0:
		details = (result.stderr or result.stdout).strip()
		raise RuntimeError(f"LaTeX compilation failed for '{tex_path}': {details}")

	pdf_path = output_path / f"{tex_path.stem}.pdf"

	if cleanup:
		cleanup_command = [
			compiler_command,
			"-c",
			"-outdir=" + str(output_path),
			str(tex_path),
		]
		cleanup_result = subprocess.run(
			cleanup_command,
			cwd=None,
			env=env,
			check=False,
			capture_output=True,
			text=True,
		)
		if cleanup_result.returncode != 0:
			details = (cleanup_result.stderr or cleanup_result.stdout).strip()
			raise RuntimeError(f"LaTeX cleanup failed for '{tex_path}': {details}")

	return str(pdf_path)


__all__ = [
	"compile_tex_file",
]
