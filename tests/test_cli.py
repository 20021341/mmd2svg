"""Test CLI entrypoint qua subprocess thật (mmd2svg.cli:main), không mock."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "mermaid_samples"


def test_cli_writes_html_file(tmp_path):
    output = tmp_path / "out.html"
    result = subprocess.run(
        [sys.executable, "-m", "mmd2svg.cli", str(FIXTURES_DIR / "flowchart.mmd"), "-o", str(output)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, result.stderr
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "<svg" in content


def test_cli_dark_skin_flag(tmp_path):
    output = tmp_path / "out_dark.html"
    result = subprocess.run(
        [sys.executable, "-m", "mmd2svg.cli", str(FIXTURES_DIR / "quadrant.mmd"), "-o", str(output), "--skin", "dark"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, result.stderr
    content = output.read_text(encoding="utf-8")
    assert "#f5f5f5" in content  # dark skin ink token xuất hiện đâu đó trong style/svg


def test_cli_out_of_scope_exits_nonzero_with_stderr_message(tmp_path):
    output = tmp_path / "should_not_exist.html"
    result = subprocess.run(
        [sys.executable, "-m", "mmd2svg.cli", str(FIXTURES_DIR / "out_of_scope_er.mmd"), "-o", str(output)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode != 0
    assert "ngoài phạm vi" in result.stderr
    assert not output.exists()
