"""Intermediate Representation (IR) — kết quả của Parser.

Tuyệt đối không có toạ độ hay màu sắc. Field dùng chung duy nhất: `warnings`.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IR:
    title: str | None = None
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Flowchart (graph-based)
# ---------------------------------------------------------------------------


@dataclass
class FNode:
    id: str
    label: str
    shape: str = "rect"  # "oval" (start/end) | "rect" (step) | "diamond" (decision)


@dataclass
class FEdge:
    source: str
    target: str
    label: str | None = None


@dataclass
class FlowChartIR(IR):
    nodes: list[FNode] = field(default_factory=list)
    edges: list[FEdge] = field(default_factory=list)


# ---------------------------------------------------------------------------
# State machine (graph-based)
# ---------------------------------------------------------------------------


@dataclass
class SNode:
    id: str
    label: str
    is_start: bool = False
    is_end: bool = False


@dataclass
class STransition:
    source: str
    target: str
    label: str | None = None


@dataclass
class StateMachineIR(IR):
    states: list[SNode] = field(default_factory=list)
    transitions: list[STransition] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Sequence (formulaic)
# ---------------------------------------------------------------------------


@dataclass
class Actor:
    id: str
    label: str


@dataclass
class Message:
    source: str
    target: str
    label: str
    kind: str = "call"  # "call" | "return" | "self"


@dataclass
class SequenceIR(IR):
    actors: list[Actor] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Timeline (formulaic)
# ---------------------------------------------------------------------------


@dataclass
class TimelineEvent:
    label: str
    period: str  # nhãn thời gian gốc từ Mermaid (vd "2024 Q1")
    is_milestone: bool = False


@dataclass
class TimelineIR(IR):
    title: str | None = None
    events: list[TimelineEvent] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Quadrant (formulaic)
# ---------------------------------------------------------------------------


@dataclass
class QuadrantItem:
    label: str
    x: float  # 0..1
    y: float  # 0..1


@dataclass
class QuadrantIR(IR):
    title: str | None = None
    x_label_low: str = ""
    x_label_high: str = ""
    y_label_low: str = ""
    y_label_high: str = ""
    items: list[QuadrantItem] = field(default_factory=list)
