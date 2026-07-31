import xml.etree.ElementTree as ET

from mmd2svg.layout import Rect, TimelineCardPos, TimelineHeaderPos, TimelineLayout, TimelineStemPos
from mmd2svg.renderers.timeline import TimelineRenderer
from mmd2svg.theme import Theme


def _hand_built_layout() -> TimelineLayout:
    return TimelineLayout(
        viewbox_w=400,
        viewbox_h=320,
        axis_y=100,
        axis_start_x=24,
        axis_end_x=376,
        headers=[
            TimelineHeaderPos(period="2022", rect=Rect(40, 40, 150, 40)),
            TimelineHeaderPos(period="2023", rect=Rect(210, 40, 150, 40), is_milestone=True),
        ],
        stems=[
            TimelineStemPos(x=115, y1=80, y2=200),
            TimelineStemPos(x=285, y1=80, y2=200, is_milestone=True),
        ],
        cards=[
            TimelineCardPos(label="v1", rect=Rect(40, 120, 150, 44)),
            TimelineCardPos(label="v2", rect=Rect(210, 120, 150, 44), is_milestone=True),
        ],
    )


def test_renderer_canvas_holds_single_theme_instance():
    layout = _hand_built_layout()
    theme = Theme.load("dark")
    canvas = TimelineRenderer().render(layout, theme)
    assert canvas.theme is theme


def test_renderer_output_valid_svg_viewbox_matches():
    layout = _hand_built_layout()
    canvas = TimelineRenderer().render(layout, Theme.load("light"))
    svg = canvas.to_svg()
    root = ET.fromstring(svg)
    assert root.attrib["viewBox"] == f"0 0 {layout.viewbox_w} {layout.viewbox_h}"


def test_renderer_milestone_uses_accent_regular_uses_ink():
    layout = _hand_built_layout()
    theme = Theme.load("light")
    canvas = TimelineRenderer().render(layout, theme)
    svg = canvas.to_svg()
    assert f'fill="{theme.accent}"' in svg
    assert f'fill="{theme.ink}"' in svg
