"""Renderer cho flowchart. Shape carries type, không dùng màu để phân biệt shape."""
from __future__ import annotations

from mmd2svg.base import Renderer
from mmd2svg.layout import FlowChartLayout
from mmd2svg.renderers.primitives import (
    arrow_label,
    arrow_path,
    diamond_node,
    node_label,
    oval_node,
    rect_node,
)
from mmd2svg.theme import Canvas, Theme


class FlowChartRenderer(Renderer):
    def render(self, layout: FlowChartLayout, theme: Theme) -> Canvas:
        canvas = Canvas(layout.viewbox_w, layout.viewbox_h, theme)
        canvas.add_arrow_markers()

        # Vẽ cạnh trước để z-order nằm dưới node (mục 6 style guide).
        for r in layout.routes:
            marker = "arrow"
            canvas.add(arrow_path(r, theme.muted, marker=marker))
            if r.label:
                mid = r.points[len(r.points) // 2]
                canvas.add(arrow_label(mid.x, mid.y, r.label, theme.paper, theme.muted))

        for node_id, rect in layout.rects.items():
            shape = layout.shapes.get(node_id, "rect")
            if shape == "oval":
                canvas.add(oval_node(rect, theme.paper, theme.ink))
            elif shape == "diamond":
                canvas.add(diamond_node(rect, theme.paper, theme.ink))
            else:
                canvas.add(rect_node(rect, "#ffffff", theme.ink))
            canvas.add(node_label(rect.cx, rect.cy, layout.labels.get(node_id, node_id), theme.ink))

        return canvas
