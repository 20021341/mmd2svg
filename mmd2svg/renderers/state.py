"""Renderer cho state machine."""
from __future__ import annotations

from mmd2svg.base import Renderer
from mmd2svg.layout import Point, StateMachineLayout
from mmd2svg.renderers.primitives import (
    arrow_label,
    arrow_path,
    filled_dot,
    node_label,
    rect_node,
    ringed_dot,
)
from mmd2svg.theme import Canvas, Theme


class StateMachineRenderer(Renderer):
    def render(self, layout: StateMachineLayout, theme: Theme) -> Canvas:
        canvas = Canvas(layout.viewbox_w, layout.viewbox_h, theme)
        canvas.add_arrow_markers()

        for r in layout.routes:
            canvas.add(arrow_path(r, theme.muted))
            if r.label:
                anchor = _label_anchor(r)
                canvas.add(arrow_label(anchor.x, anchor.y, r.label, theme.paper, theme.muted))

        starts = set(layout.starts)
        ends = set(layout.ends)

        for node_id, rect in layout.rects.items():
            if node_id in starts:
                canvas.add(filled_dot(rect.cx, rect.cy, theme.ink, r=6))
            elif node_id in ends:
                canvas.add(ringed_dot(rect.cx, rect.cy, theme.ink, theme.ink))
            else:
                canvas.add(rect_node(rect, "#ffffff", theme.ink, rx=8))
                canvas.add(node_label(rect.cx, rect.cy, layout.labels.get(node_id, node_id), theme.ink))

        return canvas


def _label_anchor(route) -> Point:
    """Vị trí đặt label: ưu tiên về phía NGUỒN của mũi tên — nếu đường nối
    sang phải thì label ở phía trái (gần source), nếu sang trái thì ở phía
    phải. Tránh đặt trùng lên node đích (lỗi cũ: points[len//2] với đường
    thẳng 2 điểm chính là endpoint nằm trên node đích).

    Với đường có lane riêng (cặp 2 chiều), điểm giữa của đoạn ngang nằm
    trên chính lane đó — không đè lên node nào.
    """
    pts = route.points
    if len(pts) < 2:
        return pts[0]

    # Đường ngang thuần (mọi điểm cùng y): trung điểm của full span.
    if all(p.y == pts[0].y for p in pts):
        return Point((pts[0].x + pts[-1].x) / 2, pts[0].y)

    # Tìm đoạn ngang dài nhất (thường là đoạn chạy chính giữa 2 node).
    best = (0, 1)
    best_len = -1
    for i in range(len(pts) - 1):
        dx = abs(pts[i + 1].x - pts[i].x)
        if dx > best_len:
            best_len = dx
            best = (i, i + 1)

    i, j = best
    mid_x = (pts[i].x + pts[j].x) / 2
    mid_y = (pts[i].y + pts[j].y) / 2

    # Lệch về phía nguồn dọc theo đoạn ngang: nếu đi phải (dst.x > src.x),
    # đặt label gần phía trái; ngược lại gần phía phải — nhưng luôn trong
    # khoảng giữa 2 node, không tràn ra ngoài.
    src, dst = pts[0], pts[-1]
    if src.x != dst.x:
        # Nếu đoạn ngang dài nhất chạy từ source tới gần destination (không
        # có đoạn dọc nào), mid đã là trung điểm thật — không lệch thêm.
        has_vertical = any(
            pts[k].x == pts[k + 1].x for k in range(len(pts) - 1)
        )
        if has_vertical:
            if dst.x > src.x:
                mid_x = max(mid_x, src.x + 8)
            else:
                mid_x = min(mid_x, src.x - 8)
    return Point(mid_x, mid_y)
