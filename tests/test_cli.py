from __future__ import annotations

from latexcv import cli


def test_cli_rejects_wrong_output_extension(capsys):
    exit_code = cli.main([
        "examples/full-showcase/data",
        "--output",
        "invalid.tex",
    ])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "--output must use '.pdf' extension" in captured.err


def test_cli_tex_only_skips_compile(monkeypatch):
    calls: dict[str, object] = {}

    def fake_render_tex_file(**kwargs):
        calls["render_kwargs"] = kwargs
        return "out.tex"

    def fake_compile_tex_file(**kwargs):
        calls["compile_called"] = True
        raise AssertionError("compile_tex_file should not be called for --tex-only")

    monkeypatch.setattr(cli, "render_tex_file", fake_render_tex_file)
    monkeypatch.setattr(cli, "compile_tex_file", fake_compile_tex_file)

    exit_code = cli.main([
        "examples/full-showcase/data",
        "--tex-only",
        "--lang",
        "en",
        "--no-format-output",
    ])

    assert exit_code == 0
    assert calls["render_kwargs"]["format_output"] is False
    assert "compile_called" not in calls
