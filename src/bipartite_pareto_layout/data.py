"""MovieLensデータの読み込みと検証用サブグラフの抽出。"""

import networkx as nx


def load_movielens_graph(path):
    edges = []
    with open(path, "r") as f:
        for line in f:
            nums = list(map(int, line.split()))
            user_id = nums[0]
            movie_ids = nums[1:]
            for movie_id in movie_ids:
                edges.append((f"u_{user_id}", f"m_{movie_id}"))

    G = nx.Graph()
    G.add_edges_from(edges)
    return G


def build_small_subgraph(M, n_seed_movies=5, n_users_per_movie=20,
                          n_movies_per_user=5, n_focus_users=10,
                          n_movies_per_focus_user=3):
    movie_nodes = [n for n in M.nodes() if n.startswith("m_")]
    movie_degrees = sorted(movie_nodes, key=lambda n: M.degree(n), reverse=True)

    seed_movies = movie_degrees[:n_seed_movies]
    subgraph_nodes = set(seed_movies)

    for movie in seed_movies:
        users = list(M.neighbors(movie))
        subgraph_nodes.update(users[:n_users_per_movie])
        for user in users[:n_users_per_movie]:
            other_movies = list(M.neighbors(user))
            subgraph_nodes.update(other_movies[:n_movies_per_user])

    subgraph = M.subgraph(subgraph_nodes)

    sub_movie_nodes = [n for n in subgraph.nodes() if n.startswith("m_")]
    top_movie = max(sub_movie_nodes, key=lambda n: subgraph.degree(n))

    small_nodes = {top_movie}
    users = list(subgraph.neighbors(top_movie))[:n_focus_users]
    small_nodes.update(users)
    for user in users:
        movies = list(subgraph.neighbors(user))[:n_movies_per_focus_user]
        small_nodes.update(movies)

    return subgraph.subgraph(small_nodes).copy()
