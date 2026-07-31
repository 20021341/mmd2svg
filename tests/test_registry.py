import pytest

from mmd2svg.registry import REGISTRY, UnsupportedDiagramError, detect_diagram_type, get_pipeline


def test_registry_has_all_5_supported_types_with_full_triple():
    expected = {"flowchart", "sequence", "state", "timeline", "quadrant"}
    assert set(REGISTRY.keys()) == expected
    for name, (p, lb, r) in REGISTRY.items():
        assert p is not None and lb is not None and r is not None


@pytest.mark.parametrize(
    "text,expected_type",
    [
        ("flowchart TD\n  A --> B", "flowchart"),
        ("graph LR\n  A --> B", "flowchart"),
        ("sequenceDiagram\n  A->>B: hi", "sequence"),
        ("stateDiagram-v2\n  [*] --> A", "state"),
        ("timeline\n  2022 : v1", "timeline"),
        ("quadrantChart\n  A: [0.1, 0.1]", "quadrant"),
    ],
)
def test_detect_diagram_type_for_supported_syntax(text, expected_type):
    assert detect_diagram_type(text) == expected_type


def test_detect_diagram_type_out_of_scope_raises_clear_error():
    with pytest.raises(UnsupportedDiagramError, match="ngoài phạm vi"):
        detect_diagram_type("erDiagram\n  CUSTOMER ||--o{ ORDER : places")


def test_detect_diagram_type_unknown_raises_clear_error():
    with pytest.raises(UnsupportedDiagramError):
        detect_diagram_type("not a real diagram header")


def test_get_pipeline_unknown_type_raises():
    with pytest.raises(UnsupportedDiagramError):
        get_pipeline("gantt")


def test_get_pipeline_returns_matching_triple():
    parser, layout_builder, renderer = get_pipeline("flowchart")
    from mmd2svg.parsers.flowchart import FlowChartParser
    assert isinstance(parser, FlowChartParser)
