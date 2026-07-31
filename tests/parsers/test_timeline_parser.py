from mmd2svg.parsers.timeline import TimelineParser


def test_minimal_single_event():
    ir = TimelineParser().parse("timeline\n  2022 : v1 launch")
    assert len(ir.events) == 1
    assert ir.events[0].period == "2022"
    assert ir.events[0].label == "v1 launch"
    assert ir.warnings == []


def test_full_syntax_title_multi_event_milestone():
    text = """
    timeline
      title Release history
      2022 : v1 launch
      !2023 : v2 launch
      2024 : v3 launch : v3.1 patch
    """
    ir = TimelineParser().parse(text)
    assert ir.title == "Release history"
    assert len(ir.events) == 4
    milestone = next(e for e in ir.events if e.period == "2023")
    assert milestone.is_milestone is True
    v3_events = [e for e in ir.events if e.period == "2024"]
    assert {e.label for e in v3_events} == {"v3 launch", "v3.1 patch"}
    assert ir.warnings == []


def test_unrecognized_syntax_produces_warning():
    ir = TimelineParser().parse("timeline\n  no colon here")
    assert len(ir.warnings) >= 1


def test_over_budget_events_warning():
    lines = ["timeline"] + [f"  {2000+i} : Event {i}" for i in range(13)]
    ir = TimelineParser().parse("\n".join(lines))
    assert any("phức tạp" in w for w in ir.warnings)


def test_parser_never_sets_coordinates():
    ir = TimelineParser().parse("timeline\n  2022 : launch")
    assert not hasattr(ir, "x")
    assert not hasattr(ir, "baseline_y")
