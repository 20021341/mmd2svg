import xml.etree.ElementTree as ET

from mmd2svg.layout import Activation, MessageRoute, SequenceLayout
from mmd2svg.renderers.sequence import SequenceRenderer
from mmd2svg.theme import Theme


def _hand_built_layout() -> SequenceLayout:
    return SequenceLayout(
        viewbox_w=400,
        viewbox_h=300,
        actor_x={"A": 100, "B": 260},
        labels={"A": "Client", "B": "Server"},
        lifeline_top=80,
        lifeline_bottom=260,
        messages=[
            MessageRoute(source="A", target="B", label="Request", y=120, kind="call"),
            MessageRoute(source="B", target="A", label="Response", y=170, kind="return"),
        ],
        activations=[Activation(actor="A", y_start=120, y_end=170)],
    )


def test_renderer_canvas_holds_single_theme_instance():
    layout = _hand_built_layout()
    theme = Theme.load("light")
    canvas = SequenceRenderer().render(layout, theme)
    assert canvas.theme is theme


def test_renderer_output_valid_svg_viewbox_matches():
    layout = _hand_built_layout()
    canvas = SequenceRenderer().render(layout, Theme.load("light"))
    svg = canvas.to_svg()
    root = ET.fromstring(svg)
    assert root.attrib["viewBox"] == f"0 0 {layout.viewbox_w} {layout.viewbox_h}"


def test_renderer_lifeline_dashed_and_return_message_dashed():
    layout = _hand_built_layout()
    canvas = SequenceRenderer().render(layout, Theme.load("light"))
    svg = canvas.to_svg()
    assert 'stroke-dasharray="3,3"' in svg  # lifeline
    assert 'stroke-dasharray="5,4"' in svg  # return message


def test_renderer_actor_labels_present():
    layout = _hand_built_layout()
    canvas = SequenceRenderer().render(layout, Theme.load("light"))
    svg = canvas.to_svg()
    assert "Client" in svg
    assert "Server" in svg
