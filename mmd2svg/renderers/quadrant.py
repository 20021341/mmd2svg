"""Renderer cho quadrant. Jobs-minimal axis labels: 1 từ, uppercase, không glyph."""
from __future__ import annotations

from mmd2svg.base import Renderer
from mmd2svg.layout import QuadrantLayout
from mmd2svg.renderers.primitives import axis_cross, axis_label_tip, quadrant_item_dot
from mmd2svg.theme import Canvas, Theme

ARROW_MARGIN = 20


def _first_word(text: str) -> str:
    words = text.strip().split()
    return words[0] if words else ""


class QuadrantRenderer(Renderer):
    def render(self, layout: QuadrantLayout, theme: Theme) -> Canvas:
        canvas = Canvas(layout.viewbox_w, layout.viewbox_h, theme)
        canvas.add_arrow_markers()

        arrow_half_w = layout.half_w + ARROW_MARGIN
        arrow_half_h = layout.half_h + ARROW_MARGIN
        canvas.add(axis_cross(layout.center_x, layout.center_y, arrow_half_w, arrow_half_h, theme.ink))

        canvas.add(axis_label_tip(
            layout.center_x, layout.center_y - arrow_half_h - 12,
            _first_word(layout.y_label_high), theme.ink, "middle",
        ))
        canvas.add(axis_label_tip(
            layout.center_x, layout.center_y + arrow_half_h + 20,
            _first_word(layout.y_label_low), theme.ink, "middle",
        ))
        canvas.add(axis_label_tip(
            layout.center_x - arrow_half_w - 12, layout.center_y,
            _first_word(layout.x_label_low), theme.ink, "end", "middle",
        ))
        canvas.add(axis_label_tip(
            layout.center_x + arrow_half_w + 12, layout.center_y,
            _first_word(layout.x_label_high), theme.ink, "start", "middle",
        ))

        for item in layout.items:
            canvas.add(quadrant_item_dot(item.x, item.y, item.label, theme.muted, theme.ink))

        return canvas
