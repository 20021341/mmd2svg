from mmd2svg.parsers.sequence import SequenceParser


def test_minimal_single_actor_no_message():
    ir = SequenceParser().parse("sequenceDiagram\n  participant A")
    assert [a.id for a in ir.actors] == ["A"]
    assert ir.messages == []
    assert ir.warnings == []


def test_full_syntax_call_return_self_and_alias():
    text = """
    sequenceDiagram
      participant A as Client
      participant B as Server
      A->>B: Request
      B-->>A: Response
      A->>A: Self check
    """
    ir = SequenceParser().parse(text)
    by_id = {a.id: a for a in ir.actors}
    assert by_id["A"].label == "Client"
    assert by_id["B"].label == "Server"

    kinds = {(m.source, m.target, m.label): m.kind for m in ir.messages}
    assert kinds[("A", "B", "Request")] == "call"
    assert kinds[("B", "A", "Response")] == "return"
    assert kinds[("A", "A", "Self check")] == "self"
    assert ir.warnings == []


def test_actor_inferred_from_message_without_participant_declaration():
    text = "sequenceDiagram\n  A->>B: hi"
    ir = SequenceParser().parse(text)
    ids = {a.id for a in ir.actors}
    assert ids == {"A", "B"}


def test_unrecognized_syntax_produces_warning():
    text = "sequenceDiagram\n  ??? garbage"
    ir = SequenceParser().parse(text)
    assert len(ir.warnings) >= 1


def test_over_budget_actors_warning():
    lines = ["sequenceDiagram"] + [f"  participant P{i}" for i in range(6)]
    ir = SequenceParser().parse("\n".join(lines))
    assert any("phức tạp" in w for w in ir.warnings)


def test_parser_never_sets_coordinates():
    ir = SequenceParser().parse("sequenceDiagram\n  A->>B: hi")
    assert not hasattr(ir, "x")
    assert not hasattr(ir, "actor_x")
