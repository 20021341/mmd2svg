import itertools

from mmd2svg.ir import FEdge, FlowChartIR, FNode
from mmd2svg.layout_builders.flowchart import FlowChartLayoutBuilder


def assert_no_rect_overlap(rects):
    for id_a, id_b in itertools.combinations(rects, 2):
        assert not rects[id_a].intersects(rects[id_b]), f"{id_a} overlaps {id_b}"


def assert_no_route_crosses_unrelated_node(route_obj, rects):
    endpoints = {route_obj.source, route_obj.target}
    for node_id, rect in rects.items():
        if node_id in endpoints:
            continue
        assert not route_obj.intersects(rect), (
            f"edge {route_obj.source}->{route_obj.target} crosses {node_id}"
        )


def _ir(nodes, edges):
    return FlowChartIR(
        nodes=[FNode(id=n, label=n) for n in nodes],
        edges=[FEdge(source=s, target=t) for s, t in edges],
    )


def test_layout_builder_linear_chain_no_overlap():
    ir = _ir(["A", "B", "C"], [("A", "B"), ("B", "C")])
    layout = FlowChartLayoutBuilder().layout(ir)
    assert set(layout.rects) == {"A", "B", "C"}
    assert_no_rect_overlap(layout.rects)
    for r in layout.routes:
        assert_no_route_crosses_unrelated_node(r, layout.rects)
    assert layout.viewbox_w > 0 and layout.viewbox_h > 0


def test_layout_builder_branching_no_overlap():
    ir = _ir(
        ["A", "B", "C", "D", "E"],
        [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("D", "E")],
    )
    layout = FlowChartLayoutBuilder().layout(ir)
    assert_no_rect_overlap(layout.rects)
    for r in layout.routes:
        assert_no_route_crosses_unrelated_node(r, layout.rects)


def test_layout_builder_cycle_still_produces_layout():
    ir = _ir(["A", "B", "C"], [("A", "B"), ("B", "C"), ("C", "A")])
    layout = FlowChartLayoutBuilder().layout(ir)
    assert set(layout.rects) == {"A", "B", "C"}
    assert_no_rect_overlap(layout.rects)
    # back-edge C->A phải được vẽ nét đứt.
    back_route = next(r for r in layout.routes if r.source == "C" and r.target == "A")
    assert back_route.dashed is True


def test_layout_builder_diamond_bigger_than_rect():
    ir = _ir(["A", "B"], [("A", "B")])
    ir.nodes[1].shape = "diamond"
    layout = FlowChartLayoutBuilder().layout(ir)
    assert layout.rects["B"].h > layout.rects["A"].h


def test_layout_builder_empty_ir():
    ir = FlowChartIR(nodes=[], edges=[])
    layout = FlowChartLayoutBuilder().layout(ir)
    assert layout.rects == {}
    assert layout.routes == []
