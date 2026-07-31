import xml.etree.ElementTree as ET

from mmd2svg.layout import EdgeRoute, FlowChartLayout, Point, Rect
from mmd2svg.renderers.flowchart import FlowChartRenderer
from mmd2svg.theme import Theme


def _hand_built_layout() -> FlowChartLayout:
    return FlowChartLayout(
        viewbox_w=400,
        viewbox_h=200,
        rects={
            "A": Rect(20, 20, 140, 48),
            "B": Rect(220, 20, 140, 64),
        },
        shapes={"A": "oval", "B": "diamond"},
        labels={"A": "Start", "B": "Is valid?"},
        routes=[
            EdgeRoute(source="A", target="B", points=[Point(160, 44), Point(220, 52)], label="go"),
        ],
    )


def test_renderer_uses_theme_paper_and_ink_correctly():
    layout = _hand_built_layout()
    light = Theme.load("light")
    canvas = FlowChartRenderer().render(layout, light)
    svg = canvas.to_svg()
    assert light.ink in svg
    # style-guide: node không focal (không phải accent-tint) -> node fill dùng paper hoặc trắng,
    # không dùng accent. Kiểm tra node oval (A) dùng đúng paper làm fill.
    assert f'fill="{light.paper}" stroke="{light.ink}"' in svg


def test_renderer_canvas_holds_single_theme_instance():
    layout = _hand_built_layout()
    theme = Theme.load("dark")
    canvas = FlowChartRenderer().render(layout, theme)
    assert canvas.theme is theme


def test_renderer_output_is_valid_svg_and_viewbox_matches():
    layout = _hand_built_layout()
    canvas = FlowChartRenderer().render(layout, Theme.load("light"))
    svg = canvas.to_svg()
    root = ET.fromstring(svg)  # không lỗi parse
    assert root.attrib["viewBox"] == f"0 0 {layout.viewbox_w} {layout.viewbox_h}"


def test_renderer_shapes_render_distinct_elements():
    layout = _hand_built_layout()
    canvas = FlowChartRenderer().render(layout, Theme.load("light"))
    svg = canvas.to_svg()
    assert "<ellipse" in svg  # oval
    assert "<polygon" in svg  # diamond
