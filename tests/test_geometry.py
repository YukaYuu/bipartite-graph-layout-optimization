import networkx as nx
import numpy as np
import pytest

from bipartite_pareto_layout.geometry import (
    calc_edge_crossings,
    calc_edge_length_uniformity,
    calc_layout_quality,
    pos_from_x,
    precompute_edge_structure,
    segments_intersect,
)


def test_segments_intersect_detects_x_crossing():
    # (0,0)-(1,1) と (0,1)-(1,0) は中央で交差するX字
    p1 = np.array([[0.0, 0.0]])
    p2 = np.array([[1.0, 1.0]])
    p3 = np.array([[0.0, 1.0]])
    p4 = np.array([[1.0, 0.0]])
    assert segments_intersect(p1, p2, p3, p4)[0]


def test_segments_intersect_parallel_lines_do_not_cross():
    p1 = np.array([[0.0, 0.0]])
    p2 = np.array([[1.0, 0.0]])
    p3 = np.array([[0.0, 1.0]])
    p4 = np.array([[1.0, 1.0]])
    assert not segments_intersect(p1, p2, p3, p4)[0]


def test_calc_edge_crossings_known_crossing_graph():
    """
    m_1-u_1とm_2-u_2の2本のエッジだけを、位置を交差するように配置すれば、
    交差率は必ず1.0(唯一のノード非共有ペアが交差)になる。
    """
    G = nx.Graph()
    G.add_edge("m_1", "u_1")
    G.add_edge("m_2", "u_2")
    pre = precompute_edge_structure(G)
    assert len(pre["pair_i"]) == 1  # 2エッジ中、ノードを共有しないペアは1組だけ

    pos = {"m_1": np.array([0.0, 0.0]), "u_1": np.array([1.0, 1.0]),
           "m_2": np.array([0.0, 1.0]), "u_2": np.array([1.0, 0.0])}
    assert calc_edge_crossings(pos, pre) == 1.0


def test_calc_edge_crossings_no_shared_node_pairs_returns_zero():
    """全エッジが1つのノードを共有する(スター型)場合、判定対象ペアが無いので0.0。"""
    G = nx.Graph()
    G.add_edges_from([("center", "a"), ("center", "b"), ("center", "c")])
    pre = precompute_edge_structure(G)
    assert len(pre["pair_i"]) == 0
    pos = {"center": np.array([0.5, 0.5]), "a": np.array([0.0, 0.0]),
           "b": np.array([1.0, 0.0]), "c": np.array([0.5, 1.0])}
    assert calc_edge_crossings(pos, pre) == 0.0


def test_calc_edge_length_uniformity_zero_when_all_edges_equal_length():
    # 正方形の4辺は全て同じ長さなので、変動係数(std/mean)は0になるはず
    square = nx.Graph()
    square.add_edges_from([("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")])
    pos = {"a": np.array([0.0, 0.0]), "b": np.array([1.0, 0.0]),
           "c": np.array([1.0, 1.0]), "d": np.array([0.0, 1.0])}
    assert calc_edge_length_uniformity(pos, square) == pytest.approx(0.0, abs=1e-9)


def test_calc_edge_length_uniformity_positive_when_lengths_differ():
    G = nx.Graph()
    G.add_edges_from([("a", "b"), ("b", "c")])
    pos = {"a": np.array([0.0, 0.0]), "b": np.array([1.0, 0.0]), "c": np.array([1.0, 5.0])}
    assert calc_edge_length_uniformity(pos, G) > 0.0


def test_calc_layout_quality_near_zero_at_ideal_length_no_overlap():
    G = nx.Graph()
    G.add_edge("a", "b")
    ideal = 0.15
    pos = {"a": np.array([0.0, 0.0]), "b": np.array([ideal, 0.0])}
    assert calc_layout_quality(pos, G, ideal_edge_length=ideal) < 1e-9


def test_pos_from_x_round_trips_coordinates():
    nodes = ["a", "b", "c"]
    x = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    pos = pos_from_x(x, nodes)
    assert np.allclose(pos["a"], [0.1, 0.2])
    assert np.allclose(pos["b"], [0.3, 0.4])
    assert np.allclose(pos["c"], [0.5, 0.6])
