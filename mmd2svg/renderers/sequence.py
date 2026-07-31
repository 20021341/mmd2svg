"""Renderer cho sequence diagram."""
from __future__ import annotations

from mmd2svg.base import Renderer
from mmd2svg.layout import SequenceLayout
from mmd2svg.renderers.primitives import (
    activation_bar,
    actor_box,
    arrow_label,
    lifeline,
    message_arrow,
    self_message_loop,
)
from mmd2svg.theme import Canvas, Theme

ACTOR_TOP = 40


class SequenceRenderer(Renderer):
    def render(self, layout: SequenceLayout, theme: Theme) -> Canvas:
        canvas = Canvas(layout.viewbox_w, layout.viewbox_h, theme)
        canvas.add_arrow_markers()

        # Lifelines trước (dưới cùng, sau actor box + trước message theo z-order thị giác).
        for cx in layout.actor_x.values():
            canvas.add(lifeline(cx, layout.lifeline_top, layout.lifeline_bottom, theme.rule_solid))

        for m in layout.messages:
            src_x = layout.actor_x.get(m.source, 0)
            dst_x = layout.actor_x.get(m.target, 0)
            stroke = theme.muted
            if m.self_loop:
                canvas.add(self_message_loop(src_x, m.y, stroke))
                canvas.add(arrow_label(src_x + 46, m.y + 12, m.label, theme.paper, theme.muted))
            else:
                dashed = m.kind == "return"
                canvas.add(message_arrow(src_x, m.y, dst_x, stroke, dashed))
                mid_x = (src_x + dst_x) / 2
                if m.label:
                    canvas.add(arrow_label(mid_x, m.y, m.label, theme.paper, theme.muted))

        for act in layout.activations:
            cx = layout.actor_x.get(act.actor, 0)
            canvas.add(activation_bar(cx, act.y_start, act.y_end, "rgba(45,49,66,0.06)", theme.muted))

        # Actor box vẽ cuối để nằm trên lifeline.
        for aid, cx in layout.actor_x.items():
            canvas.add(actor_box(cx, ACTOR_TOP, layout.labels.get(aid, aid),
                                  "#ffffff", theme.ink, theme.ink))

        return canvas
