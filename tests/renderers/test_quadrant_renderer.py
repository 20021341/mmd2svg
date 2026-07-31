import xml.etree.ElementTree as ET

from mmd2svg.layout import QuadrantItemPos, QuadrantLayout
from mmd2svg.renderers.quadrant import QuadrantRenderer
from mmd2svg.theme import Theme


def _hand_built_layout() -> QuadrantLayout:
    return QuadrantLayout(
        viewbox_w=600,
        viewbox_h=440,
        center_x=300,
        center_y=220,
        half_w=220,
        half_h=160,
        x_label_low="Low Effort",
        x_label_high="High Effort",
        y_label_low="Low Reach",
        y_label_high="High Reach",
        items=[QuadrantItemPos(label="Item A", x=380, y=140)],
    )


def test_renderer_canvas_holds_single_theme_instance():
    layout = _hand_built_layout()
    theme = Theme.load("light")
    canvas = QuadrantRenderer().render(layout, theme)
    assert canvas.theme is theme


def test_renderer_output_valid_svg_viewbox_matches():
    layout = _hand_built_layout()
    canvas = QuadrantRenderer().render(layout, Theme.load("light"))
    svg = canvas.to_svg()
    root = ET.fromstring(svg)
    assert root.attrib["viewBox"] == f"0 0 {layout.viewbox_w} {layout.viewbox_h}"


def test_renderer_axis_labels_single_word_uppercase_no_glyph():
    layout = _hand_built_layout()
    canvas = QuadrantRenderer().render(layout, Theme.load("light"))
    svg = canvas.to_svg()
    assert ">LOW<" in svg or ">HIGH<" in svg
    assert "EFFORT" not in svg  # chỉ từ đầu tiên, không phải cả cụm
    assert "↑" not in svg and "→" not in svg


def test_renderer_item_label_present():
    layout = _hand_built_layout()
    canvas = QuadrantRenderer().render(layout, Theme.load("light"))
    svg = canvas.to_svg()
    assert "Item A" in svg
