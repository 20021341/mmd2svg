import itertools

from mmd2svg.ir import SNode, STransition, StateMachineIR
from mmd2svg.layout_builders.state import StateMachineLayoutBuilder
from mmd2svg.parsers.state import END_ID, START_ID


def assert_no_rect_overlap(rects):
    for id_a, id_b in itertools.combinations(rects, 2):
        assert not rects[id_a].intersects(rects[id_b]), f"{id_a} overlaps {id_b}"


def test_layout_builder_start_idle_running_end():
    ir = StateMachineIR(
        states=[
            SNode(id=START_ID, label="", is_start=True),
            SNode(id="Idle", label="Idle"),
            SNode(id="Running", label="Running"),
            SNode(id=END_ID, label="", is_end=True),
        ],
        transitions=[
            STransition(source=START_ID, target="Idle"),
            STransition(source="Idle", target="Running", label="start"),
            STransition(source="Running", target="Idle", label="stop"),
            STransition(source="Running", target=END_ID),
        ],
    )
    layout = StateMachineLayoutBuilder().layout(ir)
    assert set(layout.rects) == {START_ID, "Idle", "Running", END_ID}
    assert layout.starts == [START_ID]
    assert layout.ends == [END_ID]
    assert_no_rect_overlap(layout.rects)


def test_layout_builder_cycle_transitions_dashed():
    ir = StateMachineIR(
        states=[SNode(id="A", label="A"), SNode(id="B", label="B")],
        transitions=[
            STransition(source="A", target="B"),
            STransition(source="B", target="A"),
        ],
    )
    layout = StateMachineLayoutBuilder().layout(ir)
    back_route = next(r for r in layout.routes if r.source == "B" and r.target == "A")
    assert back_route.dashed is True


def test_layout_builder_empty_ir():
    ir = StateMachineIR(states=[], transitions=[])
    layout = StateMachineLayoutBuilder().layout(ir)
    assert layout.rects == {}
