"""LayoutBuilder cho sequence — formulaic: thứ tự actor + thứ tự dòng thời gian."""
from __future__ import annotations

from mmd2svg.base import LayoutBuilder
from mmd2svg.ir import SequenceIR
from mmd2svg.layout import Activation, MessageRoute, SequenceLayout

ACTOR_SPACING = 160
ACTOR_TOP = 40
ACTOR_BOX_W = 120  # phải khớp với renderers/primitives.py::actor_box
ROW_HEIGHT = 40
PADDING = 24
SELF_LOOP_EXTRA_W = 56  # self-loop vẽ về bên phải lifeline, cần chỗ trong viewbox
SELF_LOOP_EXTRA_ROW = 20


class SequenceLayoutBuilder(LayoutBuilder):
    def layout(self, ir: SequenceIR) -> SequenceLayout:
        if not ir.actors:
            return SequenceLayout(viewbox_w=PADDING * 2, viewbox_h=PADDING * 2)

        # actor_x[0] phải chừa đủ nửa bề rộng actor box + padding, nếu không
        # mép trái của box đầu tiên bị âm và bị cắt khỏi viewbox.
        left_margin = PADDING + ACTOR_BOX_W / 2
        actor_x = {
            a.id: left_margin + i * ACTOR_SPACING for i, a in enumerate(ir.actors)
        }

        lifeline_top = ACTOR_TOP + 40
        messages: list[MessageRoute] = []
        activations: list[Activation] = []
        y = lifeline_top + ROW_HEIGHT

        call_stack: dict[str, float] = {}  # actor -> y bắt đầu activation đang mở

        for m in ir.messages:
            is_self = m.source == m.target
            messages.append(
                MessageRoute(
                    source=m.source,
                    target=m.target,
                    label=m.label,
                    y=y,
                    kind=m.kind,
                    self_loop=is_self,
                )
            )

            if m.kind == "call" and not is_self:
                call_stack.setdefault(m.source, y)
            elif m.kind == "return" and not is_self:
                # đóng activation gần nhất mở trên actor nguồn của return (thường là target gốc)
                if m.target in call_stack:
                    activations.append(
                        Activation(actor=m.target, y_start=call_stack.pop(m.target), y_end=y)
                    )

            y += ROW_HEIGHT + (SELF_LOOP_EXTRA_ROW if is_self else 0)

        # Đóng các activation còn treo (message return bị thiếu) tại y cuối cùng.
        for actor, y_start in call_stack.items():
            activations.append(Activation(actor=actor, y_start=y_start, y_end=y))

        lifeline_bottom = y + PADDING

        # Bên phải cần chừa nửa actor box cuối; nếu actor cuối có self-message,
        # cần thêm SELF_LOOP_EXTRA_W vì self-loop vẽ lồi sang phải lifeline.
        last_actor_id = ir.actors[-1].id
        has_self_loop_on_last = any(
            m.source == m.target == last_actor_id for m in ir.messages
        )
        right_margin = ACTOR_BOX_W / 2 + (SELF_LOOP_EXTRA_W if has_self_loop_on_last else 0)
        viewbox_w = int(max(actor_x.values()) + right_margin + PADDING)
        viewbox_h = int(lifeline_bottom + PADDING)

        return SequenceLayout(
            viewbox_w=viewbox_w,
            viewbox_h=viewbox_h,
            actor_x=actor_x,
            labels={a.id: a.label for a in ir.actors},
            lifeline_top=lifeline_top,
            lifeline_bottom=lifeline_bottom,
            messages=messages,
            activations=activations,
        )
