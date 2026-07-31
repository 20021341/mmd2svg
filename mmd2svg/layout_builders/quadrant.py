"""LayoutBuilder cho quadrant — formulaic: toạ độ [0,1] đọc thẳng từ input."""
from __future__ import annotations

from mmd2svg.base import LayoutBuilder
from mmd2svg.ir import QuadrantIR
from mmd2svg.layout import QuadrantItemPos, QuadrantLayout

HALF_W = 220
HALF_H = 160
PADDING = 80  # chỗ cho arrow tip + axis label bên ngoài half box


class QuadrantLayoutBuilder(LayoutBuilder):
    def layout(self, ir: QuadrantIR) -> QuadrantLayout:
        center_x = PADDING + HALF_W
        center_y = PADDING + HALF_H

        positions = []
        for item in ir.items:
            # x=0..1 -> trái..phải quanh center; y=0..1 (mermaid: 0=dưới,1=trên) -> dưới..trên.
            px = center_x + (item.x - 0.5) * 2 * HALF_W
            py = center_y - (item.y - 0.5) * 2 * HALF_H
            positions.append(QuadrantItemPos(label=item.label, x=px, y=py))

        viewbox_w = int(center_x + HALF_W + PADDING)
        viewbox_h = int(center_y + HALF_H + PADDING)

        return QuadrantLayout(
            viewbox_w=viewbox_w,
            viewbox_h=viewbox_h,
            center_x=center_x,
            center_y=center_y,
            half_w=HALF_W,
            half_h=HALF_H,
            x_label_low=ir.x_label_low,
            x_label_high=ir.x_label_high,
            y_label_low=ir.y_label_low,
            y_label_high=ir.y_label_high,
            items=positions,
        )
