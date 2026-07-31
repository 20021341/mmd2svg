from mmd2svg.graph_engine import position


def test_position_formula_x_from_rank_y_from_order():
    rank_map = {"A": 0, "B": 1, "C": 1}
    order_map = {"A": 0, "B": 0, "C": 1}
    sizes = {"A": (100, 40), "B": (100, 40), "C": (100, 40)}
    rects = position(rank_map, order_map, sizes, col_gap=20, row_gap=10)

    col_width = 100
    row_height = 40
    assert rects["A"].x == 0 * (col_width + 20)
    assert rects["B"].x == 1 * (col_width + 20)
    assert rects["C"].x == 1 * (col_width + 20)
    # B (order 0) phải đứng trên C (order 1) trong cùng tầng.
    assert rects["B"].y < rects["C"].y
    assert rects["C"].y - rects["B"].y == row_height + 10


def test_position_centers_thinner_columns():
    # Tầng 0 có 1 node, tầng 1 có 2 node -> tầng 0 phải được căn giữa theo chiều dọc.
    rank_map = {"A": 0, "B": 1, "C": 1}
    order_map = {"A": 0, "B": 0, "C": 1}
    sizes = {"A": (100, 40), "B": (100, 40), "C": (100, 40)}
    rects = position(rank_map, order_map, sizes, col_gap=20, row_gap=10)

    total_h_layer1 = 40 * 2 + 10
    expected_a_y = (total_h_layer1 - 40) / 2
    assert rects["A"].y == expected_a_y
