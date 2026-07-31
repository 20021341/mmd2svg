from mmd2svg.parsers.state import END_ID, START_ID, StateMachineParser


def test_minimal_single_transition_with_start():
    text = "stateDiagram-v2\n  [*] --> Idle"
    ir = StateMachineParser().parse(text)
    ids = {s.id for s in ir.states}
    assert START_ID in ids
    assert "Idle" in ids
    assert ir.warnings == []


def test_full_syntax_labeled_transitions_and_end():
    text = """
    stateDiagram-v2
      [*] --> Idle
      Idle --> Running : start
      Running --> Idle : stop
      Running --> [*]
    """
    ir = StateMachineParser().parse(text)
    ids = {s.id for s in ir.states}
    assert {START_ID, END_ID, "Idle", "Running"} <= ids
    by_pair = {(t.source, t.target): t for t in ir.transitions}
    assert by_pair[("Idle", "Running")].label == "start"
    assert by_pair[("Running", "Idle")].label == "stop"
    assert by_pair[("Running", END_ID)] is not None
    assert ir.warnings == []


def test_missing_start_produces_warning():
    text = "stateDiagram-v2\n  Idle --> Running"
    ir = StateMachineParser().parse(text)
    assert any("bắt đầu" in w for w in ir.warnings)


def test_unrecognized_syntax_produces_warning():
    text = "stateDiagram-v2\n  ??? garbage ???"
    ir = StateMachineParser().parse(text)
    assert len(ir.warnings) >= 1


def test_parser_never_sets_coordinates():
    ir = StateMachineParser().parse("stateDiagram-v2\n  [*] --> A")
    assert not hasattr(ir, "x")
    assert not hasattr(ir, "rects")
