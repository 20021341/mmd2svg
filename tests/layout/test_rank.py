import pytest

from mmd2svg.graph_engine import find_back_edges, rank


def test_rank_linear_graph():
    nodes = ["A", "B", "C"]
    edges = [("A", "B"), ("B", "C")]
    r = rank(nodes, edges)
    assert r == {"A": 0, "B": 1, "C": 2}


def test_rank_convergence_uses_farthest_parent():
    # A -> C, B -> C, A -> B  =>  rank[C] phải = max(rank[A], rank[B]) + 1 = rank[B] + 1
    nodes = ["A", "B", "C"]
    edges = [("A", "C"), ("B", "C"), ("A", "B")]
    r = rank(nodes, edges)
    assert r["A"] == 0
    assert r["B"] == 1
    assert r["C"] == 2  # không phải rank[A] + 1 = 1 (cha gần nhất)


def test_rank_short_cycle_detected_as_back_edge():
    nodes = ["A", "B"]
    edges = [("A", "B"), ("B", "A")]
    back = find_back_edges(nodes, edges)
    assert ("B", "A") in back
    r = rank(nodes, edges)
    assert r["A"] == 0
    assert r["B"] == 1


def test_rank_long_cycle_detected_and_rest_still_ranked():
    nodes = ["A", "B", "C"]
    edges = [("A", "B"), ("B", "C"), ("C", "A")]
    back = find_back_edges(nodes, edges)
    assert ("C", "A") in back
    r = rank(nodes, edges)
    assert r == {"A": 0, "B": 1, "C": 2}


def test_rank_no_infinite_recursion_on_multiple_cycles():
    nodes = ["A", "B", "C", "D"]
    edges = [("A", "B"), ("B", "A"), ("C", "D"), ("D", "C"), ("A", "C")]
    r = rank(nodes, edges)
    assert set(r.keys()) == set(nodes)
    assert all(isinstance(v, int) for v in r.values())
