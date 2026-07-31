from mmd2svg.parsers.quadrant import QuadrantParser


def test_minimal_single_item():
    ir = QuadrantParser().parse("quadrantChart\n  Item A: [0.3, 0.6]")
    assert len(ir.items) == 1
    assert ir.items[0].label == "Item A"
    assert ir.items[0].x == 0.3
    assert ir.items[0].y == 0.6
    assert ir.warnings == []


def test_full_syntax_title_axes_items():
    text = """
    quadrantChart
      title Reach vs Effort
      x-axis Low Effort --> High Effort
      y-axis Low Reach --> High Reach
      Item A: [0.3, 0.6]
      Item B: [0.8, 0.9]
    """
    ir = QuadrantParser().parse(text)
    assert ir.title == "Reach vs Effort"
    assert ir.x_label_low == "Low Effort"
    assert ir.x_label_high == "High Effort"
    assert ir.y_label_low == "Low Reach"
    assert ir.y_label_high == "High Reach"
    assert len(ir.items) == 2
    assert ir.warnings == []


def test_out_of_range_coordinate_produces_warning():
    ir = QuadrantParser().parse("quadrantChart\n  Bad: [1.5, 0.2]")
    assert any("phạm vi" in w for w in ir.warnings)
    assert ir.items == []


def test_unrecognized_syntax_produces_warning():
    ir = QuadrantParser().parse("quadrantChart\n  garbage line no colon")
    assert len(ir.warnings) >= 1


def test_over_budget_items_warning():
    lines = ["quadrantChart"] + [f"  Item{i}: [0.1, 0.1]" for i in range(13)]
    ir = QuadrantParser().parse("\n".join(lines))
    assert any("phức tạp" in w for w in ir.warnings)


def test_parser_never_sets_coordinates_field_of_svg():
    ir = QuadrantParser().parse("quadrantChart\n  A: [0.1, 0.1]")
    assert not hasattr(ir, "center_x")
    assert not hasattr(ir, "half_w")
