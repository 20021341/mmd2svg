from mmd2svg.ir import TimelineEvent, TimelineIR
from mmd2svg.layout_builders.timeline import TimelineLayoutBuilder


def test_period_column_headers_and_cards():
    ir = TimelineIR(events=[
        TimelineEvent(label="v1", period="2022"),
        TimelineEvent(label="v2", period="2023"),
    ])
    layout = TimelineLayoutBuilder().layout(ir)
    assert len(layout.headers) == 2
    assert layout.headers[0].period == "2022"
    assert layout.headers[1].period == "2023"
    assert len(layout.cards) == 2


def test_stacked_cards_within_same_period():
    ir = TimelineIR(events=[
        TimelineEvent(label="v3", period="2024"),
        TimelineEvent(label="v3.1", period="2024"),
    ])
    layout = TimelineLayoutBuilder().layout(ir)
    assert len(layout.headers) == 1
    assert len(layout.cards) == 2
    assert layout.cards[0].rect.y < layout.cards[1].rect.y


def test_milestone_flag_propagated():
    ir = TimelineIR(events=[TimelineEvent(label="v2", period="2023", is_milestone=True)])
    layout = TimelineLayoutBuilder().layout(ir)
    assert layout.headers[0].is_milestone is True
    assert layout.cards[0].is_milestone is True


def test_empty_ir():
    ir = TimelineIR(events=[])
    layout = TimelineLayoutBuilder().layout(ir)
    assert layout.headers == []
    assert layout.cards == []
