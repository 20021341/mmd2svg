"""Smoke test end-to-end: mỗi fixture .mmd -> HTML hợp lệ, viewBox khớp, SVG parse được."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from mmd2svg.cli import convert
from mmd2svg.registry import REGISTRY, UnsupportedDiagramError

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "mermaid_samples"

_SUPPORTED_FIXTURES = [
    "flowchart.mmd",
    "sequence.mmd",
    "state.mmd",
    "timeline.mmd",
    "quadrant.mmd",
]

_SVG_RE = re.compile(r"<svg.*?</svg>", re.DOTALL)


@pytest.mark.parametrize("filename", _SUPPORTED_FIXTURES)
@pytest.mark.parametrize("skin", ["light", "dark"])
def test_end_to_end_fixture_produces_valid_html_and_svg(filename, skin):
    text = (FIXTURES_DIR / filename).read_text(encoding="utf-8")
    html = convert(text, skin=skin)

    assert "<!DOCTYPE html>" in html
    assert "<svg" in html and "</svg>" in html

    svg_match = _SVG_RE.search(html)
    assert svg_match, "Không tìm thấy khối <svg> trong HTML output"
    root = ET.fromstring(svg_match.group(0))  # phải parse được XML hợp lệ
    assert root.attrib["viewBox"].startswith("0 0 ")


def test_end_to_end_all_5_types_covered_by_fixtures():
    stems = {Path(f).stem for f in _SUPPORTED_FIXTURES}
    assert stems == set(REGISTRY.keys())


def test_end_to_end_out_of_scope_diagram_raises_clear_error():
    text = (FIXTURES_DIR / "out_of_scope_er.mmd").read_text(encoding="utf-8")
    with pytest.raises(UnsupportedDiagramError, match="ngoài phạm vi"):
        convert(text)
