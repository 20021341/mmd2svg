import pytest

from mmd2svg.parsers.flowchart import FlowChartParser


def test_minimal_single_node_no_edge():
    ir = FlowChartParser().parse("flowchart TD\n  A[Only node]")
    assert [n.id for n in ir.nodes] == ["A"]
    assert ir.nodes[0].label == "Only node"
    assert ir.edges == []
    assert ir.warnings == []


def test_full_syntax_shapes_and_labeled_edges():
    text = """
    flowchart TD
      A([Start]) --> B{Is valid?}
      B -->|Yes| C[Process]
      B -->|No| D((End))
      C --> D
    """
    ir = FlowChartParser().parse(text)
    by_id = {n.id: n for n in ir.nodes}
    assert by_id["A"].shape == "oval"
    assert by_id["B"].shape == "diamond"
    assert by_id["B"].label == "Is valid?"
    assert by_id["C"].shape == "rect"
    assert by_id["D"].shape == "oval"

    edge_by_pair = {(e.source, e.target): e for e in ir.edges}
    assert edge_by_pair[("B", "C")].label == "Yes"
    assert edge_by_pair[("B", "D")].label == "No"
    assert edge_by_pair[("A", "B")].label is None
    assert ir.warnings == []


def test_unrecognized_syntax_produces_warning_not_exception():
    text = "flowchart TD\n  ???not valid syntax at all%%%\n"
    ir = FlowChartParser().parse(text)
    assert len(ir.warnings) >= 1


def test_over_budget_nodes_produces_warning():
    lines = ["flowchart TD"] + [f"  N{i}[Node {i}] --> N{i+1}[Node {i+1}]" for i in range(10)]
    ir = FlowChartParser().parse("\n".join(lines))
    assert any("phức tạp" in w for w in ir.warnings)


def test_parser_never_sets_coordinates():
    ir = FlowChartParser().parse("flowchart TD\n  A --> B")
    assert not hasattr(ir, "x")
    assert not hasattr(ir, "rects")
