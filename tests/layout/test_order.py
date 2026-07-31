from mmd2svg.graph_engine import order, rank


def test_order_is_deterministic_same_input_same_output():
    nodes = ["A", "B", "C", "D"]
    edges = [("A", "C"), ("A", "D"), ("B", "C")]
    r = rank(nodes, edges)
    o1 = order(nodes, r, edges)
    o2 = order(nodes, r, edges)
    assert o1 == o2


def test_order_shared_parent_children_grouped_by_barycenter():
    # Tầng 0: A, B. Tầng 1: C (con của A), D (con của B).
    # Barycenter đẩy C theo order của A, D theo order của B.
    nodes = ["A", "B", "C", "D"]
    edges = [("A", "C"), ("B", "D")]
    r = rank(nodes, edges)
    o = order(nodes, r, edges)
    # A trước B (order ban đầu), nên C nên đứng trước D ở tầng 1.
    assert o["A"] < o["B"]
    assert o["C"] < o["D"]


def test_order_covers_all_nodes():
    nodes = ["A", "B", "C", "D", "E"]
    edges = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("D", "E")]
    r = rank(nodes, edges)
    o = order(nodes, r, edges)
    assert set(o.keys()) == set(nodes)
