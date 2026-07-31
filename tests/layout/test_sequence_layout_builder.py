from mmd2svg.ir import Actor, Message, SequenceIR
from mmd2svg.layout_builders.sequence import ACTOR_SPACING, SequenceLayoutBuilder


def _ir(actor_ids, messages):
    return SequenceIR(
        actors=[Actor(id=a, label=a) for a in actor_ids],
        messages=[Message(source=s, target=t, label=lbl, kind=k) for s, t, lbl, k in messages],
    )


def test_actor_x_formula_ordered_by_declaration():
    ir = _ir(["A", "B", "C"], [])
    layout = SequenceLayoutBuilder().layout(ir)
    assert layout.actor_x["B"] - layout.actor_x["A"] == ACTOR_SPACING
    assert layout.actor_x["C"] - layout.actor_x["B"] == ACTOR_SPACING


def test_message_y_increases_with_timeline_order():
    ir = _ir(["A", "B"], [("A", "B", "req", "call"), ("B", "A", "resp", "return")])
    layout = SequenceLayoutBuilder().layout(ir)
    assert layout.messages[0].y < layout.messages[1].y


def test_activation_bar_spans_call_to_return():
    ir = _ir(["A", "B"], [("A", "B", "req", "call"), ("B", "A", "resp", "return")])
    layout = SequenceLayoutBuilder().layout(ir)
    assert len(layout.activations) == 1
    act = layout.activations[0]
    assert act.actor == "A"  # return target = A -> đóng activation của A
    assert act.y_end > act.y_start


def test_self_message_flagged():
    ir = _ir(["A"], [("A", "A", "check", "self")])
    layout = SequenceLayoutBuilder().layout(ir)
    assert layout.messages[0].self_loop is True


def test_empty_ir():
    ir = SequenceIR(actors=[], messages=[])
    layout = SequenceLayoutBuilder().layout(ir)
    assert layout.actor_x == {}
