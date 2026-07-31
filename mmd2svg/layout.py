"""Layout — kết quả của LayoutBuilder.

Chỉ có số (x, y, chiều rộng, chiều cao, đường đi cạnh), không có màu.
Field dùng chung cho mọi loại: `viewbox_w`, `viewbox_h`.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def intersects(self, other: "Rect") -> bool:
        return not (
            self.x2 <= other.x
            or other.x2 <= self.x
            or self.y2 <= other.y
            or other.y2 <= self.y
        )

    def contains_point(self, x: float, y: float) -> bool:
        return self.x <= x <= self.x2 and self.y <= y <= self.y2


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass
class EdgeRoute:
    source: str
    target: str
    points: list[Point]
    label: str | None = None
    dashed: bool = False  # back-edge, hoặc "transit" qua vật cản bất khả kháng

    def bbox(self) -> Rect:
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    def intersects(self, rect: Rect) -> bool:
        """True nếu bất kỳ đoạn thẳng nào của path cắt/nằm trong rect."""
        for a, b in zip(self.points, self.points[1:]):
            if _segment_intersects_rect(a, b, rect):
                return True
        return False


def _segment_intersects_rect(a: Point, b: Point, rect: Rect) -> bool:
    """Đoạn a-b là orthogonal (ngang hoặc dọc) theo quy ước elbow router."""
    seg_x0, seg_x1 = sorted((a.x, b.x))
    seg_y0, seg_y1 = sorted((a.y, b.y))
    # Bounding box của đoạn không giao rect -> chắc chắn không cắt.
    if seg_x1 < rect.x or rect.x2 < seg_x0 or seg_y1 < rect.y or rect.y2 < seg_y0:
        return False
    if a.x == b.x:  # đoạn dọc
        x = a.x
        if x <= rect.x or x >= rect.x2:
            return False
        return not (seg_y1 <= rect.y or rect.y2 <= seg_y0)
    if a.y == b.y:  # đoạn ngang
        y = a.y
        if y <= rect.y or y >= rect.y2:
            return False
        return not (seg_x1 <= rect.x or rect.x2 <= seg_x0)
    # Đoạn chéo (không nên xảy ra với elbow router) — coi bbox overlap là giao.
    return True


@dataclass
class Layout:
    viewbox_w: int = 0
    viewbox_h: int = 0


# ---------------------------------------------------------------------------
# Flowchart / State machine (graph-based) dùng chung Rect/EdgeRoute
# ---------------------------------------------------------------------------


@dataclass
class FlowChartLayout(Layout):
    rects: dict[str, Rect] = field(default_factory=dict)
    shapes: dict[str, str] = field(default_factory=dict)  # node_id -> shape
    labels: dict[str, str] = field(default_factory=dict)  # node_id -> texto hiển thị
    routes: list[EdgeRoute] = field(default_factory=list)


@dataclass
class StateMachineLayout(Layout):
    rects: dict[str, Rect] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    starts: list[str] = field(default_factory=list)
    ends: list[str] = field(default_factory=list)
    routes: list[EdgeRoute] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Sequence (formulaic)
# ---------------------------------------------------------------------------


@dataclass
class Activation:
    actor: str
    y_start: float
    y_end: float


@dataclass
class MessageRoute:
    source: str
    target: str
    label: str
    y: float
    kind: str = "call"
    self_loop: bool = False


@dataclass
class SequenceLayout(Layout):
    actor_x: dict[str, float] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    lifeline_top: float = 0
    lifeline_bottom: float = 0
    messages: list[MessageRoute] = field(default_factory=list)
    activations: list[Activation] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Timeline (formulaic)
# ---------------------------------------------------------------------------


@dataclass
class TimelineHeaderPos:
    period: str
    rect: Rect
    is_milestone: bool = False


@dataclass
class TimelineCardPos:
    label: str
    rect: Rect
    is_milestone: bool = False


@dataclass
class TimelineStemPos:
    x: float
    y1: float
    y2: float
    is_milestone: bool = False


@dataclass
class TimelineLayout(Layout):
    axis_y: float = 0
    axis_start_x: float = 0
    axis_end_x: float = 0
    headers: list[TimelineHeaderPos] = field(default_factory=list)
    stems: list[TimelineStemPos] = field(default_factory=list)
    cards: list[TimelineCardPos] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Quadrant (formulaic)
# ---------------------------------------------------------------------------


@dataclass
class QuadrantItemPos:
    label: str
    x: float
    y: float


@dataclass
class QuadrantLayout(Layout):
    center_x: float = 0
    center_y: float = 0
    half_w: float = 0
    half_h: float = 0
    x_label_low: str = ""
    x_label_high: str = ""
    y_label_low: str = ""
    y_label_high: str = ""
    items: list[QuadrantItemPos] = field(default_factory=list)
