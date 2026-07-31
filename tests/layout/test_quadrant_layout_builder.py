from mmd2svg.ir import QuadrantIR, QuadrantItem
from mmd2svg.layout_builders.quadrant import HALF_H, HALF_W, QuadrantLayoutBuilder


def test_item_at_center_maps_to_center_xy():
    ir = QuadrantIR(items=[QuadrantItem(label="Mid", x=0.5, y=0.5)])
    layout = QuadrantLayoutBuilder().layout(ir)
    assert layout.items[0].x == layout.center_x
    assert layout.items[0].y == layout.center_y


def test_item_at_top_right_positioned_correctly():
    ir = QuadrantIR(items=[QuadrantItem(label="TopRight", x=1.0, y=1.0)])
    layout = QuadrantLayoutBuilder().layout(ir)
    item = layout.items[0]
    assert item.x == layout.center_x + HALF_W
    assert item.y == layout.center_y - HALF_H  # y=1 (cao) -> phía trên (y nhỏ hơn trong SVG)


def test_axis_labels_propagated():
    ir = QuadrantIR(x_label_low="Low", x_label_high="High", y_label_low="Weak", y_label_high="Strong", items=[])
    layout = QuadrantLayoutBuilder().layout(ir)
    assert layout.x_label_low == "Low"
    assert layout.x_label_high == "High"
    assert layout.y_label_low == "Weak"
    assert layout.y_label_high == "Strong"


def test_empty_items():
    ir = QuadrantIR(items=[])
    layout = QuadrantLayoutBuilder().layout(ir)
    assert layout.items == []
