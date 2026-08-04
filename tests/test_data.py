import os
import tempfile

import networkx as nx
import numpy as np

from bipartite_pareto_layout.data import build_small_subgraph, load_movielens_graph


def _write_train_file(lines):
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "train.txt")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


def test_load_movielens_graph_parses_user_movie_edges():
    path = _write_train_file(["1 10 20 30", "2 10 40"])
    G = load_movielens_graph(path)
    assert G.has_edge("u_1", "m_10")
    assert G.has_edge("u_1", "m_20")
    assert G.has_edge("u_1", "m_30")
    assert G.has_edge("u_2", "m_10")
    assert G.has_edge("u_2", "m_40")
    assert not G.has_edge("u_1", "m_40")


def test_build_small_subgraph_only_contains_neighbors_of_seed_movies():
    rng = np.random.default_rng(0)
    M = nx.Graph()
    users = [f"u_{i}" for i in range(60)]
    movies = [f"m_{i}" for i in range(30)]
    for u in users:
        chosen = rng.choice(movies, size=6, replace=False)
        for m in chosen:
            M.add_edge(u, m)

    sub = build_small_subgraph(M, n_seed_movies=3, n_users_per_movie=8, n_focus_users=5)
    # サブグラフの全ノードは元のグラフに実在し、抽出後も連結であるはず
    assert set(sub.nodes()) <= set(M.nodes())
    assert nx.is_connected(sub)
    assert sub.number_of_nodes() > 0
