from __future__ import annotations

from pathlib import Path
import textwrap

from latexcv.render import render_tex_file
from latexcv.loader import load_blocks


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


def test_profile_address_fields_are_optional(tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        (data_dir / "profile.yaml").write_text(
                textwrap.dedent(
                        """
                        profile:
                            kind: profile
                            data:
                                name:
                                    first: Alex
                                    last: Example
                        """
                ).strip()
                + "\n",
                encoding="utf-8",
        )

        (data_dir / "contact.yaml").write_text(
                textwrap.dedent(
                        """
                        contact:
                            kind: list
                            items:
                                - type: phone
                                  icon: mobile-alt
                        """
                ).strip()
                + "\n",
                encoding="utf-8",
        )

        blocks = load_blocks(data_dir=data_dir)
        assert "profile" in blocks
        assert "contact" in blocks
