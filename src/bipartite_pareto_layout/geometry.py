"""
比較対象となる標準的な可読性指標(Purchase 1997ベース): エッジ交差数・
レイアウト品質(理想エッジ長からのズレ+ノード重なり回避)・エッジ長の均一性。
"""

import networkx as nx
import numpy as np


def precompute_edge_structure(G):
    """ノードを共有しないエッジペア(=交差判定の対象になりうるペア)を事前計算する。"""
    edges = list(G.edges())
    n = len(edges)

    pair_i, pair_j = [], []
    for i in range(n):
        ui, vi = edges[i]
        for j in range(i + 1, n):
            uj, vj = edges[j]
            if ui in (uj, vj) or vi in (uj, vj):
                continue
            pair_i.append(i)
            pair_j.append(j)

    return {
        "edges": edges,
        "pair_i": np.array(pair_i, dtype=np.int64),
        "pair_j": np.array(pair_j, dtype=np.int64),
    }


def segments_intersect(p1, p2, p3, p4):
    """線分p1-p2とp3-p4が交差するかを判定する(numpyベクトル化、複数ペア同時処理)。"""

    def cross(o, a, b):
        return (a[:, 0] - o[:, 0]) * (b[:, 1] - o[:, 1]) - \
               (a[:, 1] - o[:, 1]) * (b[:, 0] - o[:, 0])

    d1 = cross(p3, p4, p1)
    d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3)
    d4 = cross(p1, p2, p4)

    cond1 = ((d1 > 0) & (d2 < 0)) | ((d1 < 0) & (d2 > 0))
    cond2 = ((d3 > 0) & (d4 < 0)) | ((d3 < 0) & (d4 > 0))
    return cond1 & cond2


def calc_layout_quality(pos, G, ideal_edge_length=0.15):
    """理想エッジ長からのズレ(ストレス項)+ノード重なり回避のペナルティ。"""
    nodes = list(G.nodes())
    coords = np.array([pos[n] for n in nodes])
    n = len(nodes)

    diff = coords[:, None, :] - coords[None, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=-1))

    adj = nx.to_numpy_array(G, nodelist=nodes)
    iu = np.triu_indices(n, k=1)

    d = dist[iu]
    a = adj[iu]

    edge_term = np.sum(a * (d - ideal_edge_length) ** 2) / (a.sum() + 1e-9)

    min_dist = ideal_edge_length * 0.5
    overlap_penalty = np.sum((1 - a) * np.maximum(0, min_dist - d) ** 2) / ((1 - a).sum() + 1e-9)

    return float(edge_term + overlap_penalty)


def calc_edge_crossings(pos, pre):
    """交差するエッジペアの割合(0〜1)。"""
    pair_i, pair_j = pre["pair_i"], pre["pair_j"]
    if len(pair_i) == 0:
        return 0.0

    edges = pre["edges"]
    coords = {n: np.asarray(p) for n, p in pos.items()}

    p1 = np.array([coords[edges[i][0]] for i in pair_i])
    p2 = np.array([coords[edges[i][1]] for i in pair_i])
    p3 = np.array([coords[edges[j][0]] for j in pair_j])
    p4 = np.array([coords[edges[j][1]] for j in pair_j])

    crossing_mask = segments_intersect(p1, p2, p3, p4)
    return float(crossing_mask.sum() / len(pair_i))


def calc_edge_length_uniformity(pos, G):
    """エッジ長の変動係数(標準偏差/平均)。小さいほど均一。"""
    edges = list(G.edges())
    lengths = []
    for u, v in edges:
        p1 = np.asarray(pos[u])
        p2 = np.asarray(pos[v])
        lengths.append(np.linalg.norm(p1 - p2))
    lengths = np.array(lengths)

    mean_len = lengths.mean()
    if mean_len < 1e-10:
        return 0.0
    return float(lengths.std() / mean_len)


def pos_from_x(x, nodes):
    """NSGA-IIの決定変数ベクトル(フラットなx,y座標列)をpos辞書に変換する。"""
    coords = x.reshape(-1, 2)
    return {node: coords[i] for i, node in enumerate(nodes)}
