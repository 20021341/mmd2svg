"""Registry — bảng ánh xạ "tên loại diagram" -> (Parser, LayoutBuilder, Renderer).

Điểm trung tâm duy nhất "biết" có bao nhiêu loại diagram được hỗ trợ (5 loại,
theo phạm vi v1). Loại nào không có trong REGISTRY -> UnsupportedDiagramError.
"""
from __future__ import annotations

import re

from mmd2svg.base import LayoutBuilder, Parser, Renderer
from mmd2svg.layout_builders.flowchart import FlowChartLayoutBuilder
from mmd2svg.layout_builders.quadrant import QuadrantLayoutBuilder
from mmd2svg.layout_builders.sequence import SequenceLayoutBuilder
from mmd2svg.layout_builders.state import StateMachineLayoutBuilder
from mmd2svg.layout_builders.timeline import TimelineLayoutBuilder
from mmd2svg.parsers.flowchart import FlowChartParser
from mmd2svg.parsers.quadrant import QuadrantParser
from mmd2svg.parsers.sequence import SequenceParser
from mmd2svg.parsers.state import StateMachineParser
from mmd2svg.parsers.timeline import TimelineParser
from mmd2svg.renderers.flowchart import FlowChartRenderer
from mmd2svg.renderers.quadrant import QuadrantRenderer
from mmd2svg.renderers.sequence import SequenceRenderer
from mmd2svg.renderers.state import StateMachineRenderer
from mmd2svg.renderers.timeline import TimelineRenderer

REGISTRY: dict[str, tuple[Parser, LayoutBuilder, Renderer]] = {
    "flowchart": (FlowChartParser(), FlowChartLayoutBuilder(), FlowChartRenderer()),
    "sequence": (SequenceParser(), SequenceLayoutBuilder(), SequenceRenderer()),
    "state": (StateMachineParser(), StateMachineLayoutBuilder(), StateMachineRenderer()),
    "timeline": (TimelineParser(), TimelineLayoutBuilder(), TimelineRenderer()),
    "quadrant": (QuadrantParser(), QuadrantLayoutBuilder(), QuadrantRenderer()),
}

# Loại Mermaid nằm ngoài phạm vi v1 (mục "Không làm các loại còn lại" của user).
_KNOWN_OUT_OF_SCOPE = {
    "er": "erDiagram",
    "gantt": "gantt",
    "pie": "pie",
    "journey": "journey",
    "mindmap": "mindmap",
    "gitgraph": "gitGraph",
    "class": "classDiagram",
}

_FIRST_TOKEN_RE = re.compile(r"^\s*%%.*$", re.MULTILINE)


class UnsupportedDiagramError(ValueError):
    """Loại diagram không nằm trong REGISTRY (ngoài phạm vi v1)."""


def detect_diagram_type(text: str) -> str:
    """Đọc dòng khai báo đầu tiên (bỏ qua comment/frontmatter/dòng trống) để suy ra loại diagram."""
    clean_text = re.sub(r"^\s*---[\s\S]*?---\s*", "", text)
    lines = [ln.strip() for ln in clean_text.splitlines() if ln.strip() and not ln.strip().startswith("%%")]
    if not lines:
        raise UnsupportedDiagramError("Input rỗng, không xác định được loại diagram")

    first = lines[0]
    first_lower = first.lower()

    if first_lower.startswith("flowchart") or first_lower.startswith("graph"):
        return "flowchart"
    if first_lower.startswith("sequencediagram"):
        return "sequence"
    if first_lower.startswith("statediagram"):
        return "state"
    if first_lower.startswith("timeline"):
        return "timeline"
    if first_lower.startswith("quadrantchart"):
        return "quadrant"

    for out_of_scope_name, header in _KNOWN_OUT_OF_SCOPE.items():
        if first_lower.startswith(header.lower()):
            raise UnsupportedDiagramError(
                f"Loại diagram '{out_of_scope_name}' (khai báo {header!r}) nằm ngoài phạm vi "
                f"hỗ trợ của mmd2svg v1. Chỉ hỗ trợ: {', '.join(sorted(REGISTRY))}."
            )

    raise UnsupportedDiagramError(
        f"Không nhận diện được loại diagram từ dòng khai báo: {first!r}. "
        f"Chỉ hỗ trợ: {', '.join(sorted(REGISTRY))}."
    )


def get_pipeline(diagram_type: str) -> tuple[Parser, LayoutBuilder, Renderer]:
    if diagram_type not in REGISTRY:
        raise UnsupportedDiagramError(
            f"Loại diagram {diagram_type!r} không có trong registry. "
            f"Chỉ hỗ trợ: {', '.join(sorted(REGISTRY))}."
        )
    return REGISTRY[diagram_type]
