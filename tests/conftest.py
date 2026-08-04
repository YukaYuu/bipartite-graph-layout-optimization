import networkx as nx
import pytest


@pytest.fixture
def small_bipartite_graph():
    """4ユーザー・3映画程度の、手で追える小さい二部グラフ。"""
    G = nx.Graph()
    G.add_edges_from([
        ("u_1", "m_1"), ("u_1", "m_2"),
        ("u_2", "m_1"), ("u_2", "m_3"),
        ("u_3", "m_2"), ("u_3", "m_3"),
        ("u_4", "m_1"),
    ])
    return G
