import xml.etree.ElementTree as ET

from mmd2svg.layout import EdgeRoute, Point, Rect, StateMachineLayout
from mmd2svg.renderers.state import StateMachineRenderer
from mmd2svg.theme import Theme


def _hand_built_layout() -> StateMachineLayout:
    return StateMachineLayout(
        viewbox_w=400,
        viewbox_h=200,
        rects={
            "__start__": Rect(20, 20, 20, 20),
            "Idle": Rect(100, 10, 140, 48),
            "__end__": Rect(300, 20, 20, 20),
        },
        labels={"Idle": "Idle"},
        starts=["__start__"],
        ends=["__end__"],
        routes=[
            EdgeRoute(source="__start__", target="Idle", points=[Point(30, 30), Point(100, 34)]),
            EdgeRoute(source="Idle", target="__end__", points=[Point(240, 34), Point(300, 30)], label="done"),
        ],
    )


def test_renderer_start_end_dots_use_ink_not_arbitrary_color():
    layout = _hand_built_layout()
    theme = Theme.load("light")
    canvas = StateMachineRenderer().render(layout, theme)
    svg = canvas.to_svg()
    assert f'fill="{theme.ink}"' in svg  # filled start dot


def test_renderer_canvas_holds_single_theme_instance():
    layout = _hand_built_layout()
    theme = Theme.load("dark")
    canvas = StateMachineRenderer().render(layout, theme)
    assert canvas.theme is theme


def test_renderer_output_valid_svg_viewbox_matches():
    layout = _hand_built_layout()
    canvas = StateMachineRenderer().render(layout, Theme.load("light"))
    svg = canvas.to_svg()
    root = ET.fromstring(svg)
    assert root.attrib["viewBox"] == f"0 0 {layout.viewbox_w} {layout.viewbox_h}"


def test_renderer_end_state_uses_ringed_dot_two_circles():
    layout = _hand_built_layout()
    canvas = StateMachineRenderer().render(layout, Theme.load("light"))
    svg = canvas.to_svg()
    assert svg.count("<circle") >= 3  # start dot + 2 vòng của end dot
