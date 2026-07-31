"""Renderer cho timeline."""
from __future__ import annotations

from mmd2svg.base import Renderer
from mmd2svg.layout import TimelineLayout
from mmd2svg.renderers.primitives import multiline_node_label, node_label, rect_node
from mmd2svg.theme import Canvas, Theme

MARGIN_X = 40


class TimelineRenderer(Renderer):
    def render(self, layout: TimelineLayout, theme: Theme) -> Canvas:
        canvas = Canvas(layout.viewbox_w, layout.viewbox_h, theme)
        canvas.add_arrow_markers()

        # 1. Trục chính ngang với mũi tên ở cuối
        canvas.add(
            f'<line x1="{layout.axis_start_x:.0f}" y1="{layout.axis_y:.0f}" '
            f'x2="{layout.axis_end_x:.0f}" y2="{layout.axis_y:.0f}" '
            f'stroke="{theme.ink}" stroke-width="2" marker-end="url(#arrow)"/>'
        )

        # 2. Đường stem dọc nối từ header card qua trục chính xuống chân event card stack
        for s in layout.stems:
            canvas.add(
                f'<line x1="{s.x:.0f}" y1="{s.y1:.0f}" x2="{s.x:.0f}" y2="{s.y2:.0f}" '
                f'stroke="{theme.soft}" stroke-width="1.5" stroke-dasharray="4,4"/>'
            )
            # Dot tròn trên trục chính tại vị trí giao với stem
            canvas.add(f'<circle cx="{s.x:.0f}" cy="{layout.axis_y:.0f}" r="5" fill="{theme.paper}" stroke="{theme.ink}" stroke-width="1.5"/>')

        # 3. Vẽ Period Header Cards ở đầu mỗi cột (đồng nhất màu theme)
        for h in layout.headers:
            canvas.add(rect_node(h.rect, theme.paper2, theme.rule_solid, rx=6))
            canvas.add(node_label(h.rect.cx, h.rect.cy, h.period, theme.ink))

        # 4. Vẽ Event Cards xếp chồng dọc phía dưới
        from mmd2svg.renderers.primitives import multiline_node_label
        for c in layout.cards:
            canvas.add(rect_node(c.rect, theme.paper, theme.rule_solid, rx=6))
            canvas.add(multiline_node_label(c.rect.cx, c.rect.cy, c.label, theme.ink))

        return canvas
