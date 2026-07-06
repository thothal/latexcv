from __future__ import annotations

from pathlib import Path

from latexcv.render import render_tex_file


def test_soft_skills_icon_lines_are_split(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "examples" / "full-showcase" / "data"

    tex_path = Path(
        render_tex_file(
            data_dir=data_dir,
            output_dir=tmp_path,
            lang="en",
            format_output=False,
        )
    )

    content = tex_path.read_text(encoding="utf-8")

    # Ensure consecutive icon-text commands are emitted on separate lines.
    assert "\\\\            \\cvicontext" not in content
    assert "\\\\\n\\cvicontext" in content or "\\\\\n    \\cvicontext" in content
