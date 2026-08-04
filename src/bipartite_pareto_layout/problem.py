"""NSGA-II(pymoo)用の多目的最適化問題の定義。"""

import numpy as np
from pymoo.core.problem import Problem

from bipartite_pareto_layout.geometry import (
    calc_edge_crossings,
    calc_edge_length_uniformity,
    calc_layout_quality,
    pos_from_x,
    precompute_edge_structure,
)


class BipartiteLayoutProblem(Problem):
    """
    3目的(交差数・レイアウト品質・エッジ長均一性)を同時に最小化する多目的最適化問題。
    決定変数は全ノードのx,y座標をフラットに並べたベクトル。
    """

    def __init__(self, graph, ideal_edge_length=0.15):
        self.graph = graph
        self.nodes = list(graph.nodes())
        self.precomputed = precompute_edge_structure(graph)
        self.ideal_edge_length = ideal_edge_length
        super().__init__(n_var=len(self.nodes) * 2, n_obj=3, xl=0.0, xu=1.0)

    def _evaluate(self, X, out, *args, **kwargs):
        raw = []
        for x in X:
            pos = pos_from_x(x, self.nodes)

            e_crossings = calc_edge_crossings(pos, self.precomputed)
            e_layout = calc_layout_quality(pos, self.graph, self.ideal_edge_length)
            e_length_uniform = calc_edge_length_uniformity(pos, self.graph)

            raw.append([e_crossings, e_layout, e_length_uniform])
        out["F"] = np.array(raw)


def make_sampling(pos, nodes, pop_size=50):
    """初期配置周辺にノイズを加えたNSGA-II用の初期集団を作る"""
    x0 = np.array([[pos[node][0], pos[node][1]] for node in nodes]).flatten()
    sampling = np.clip(
        np.vstack([x0, x0 + np.random.normal(0, 0.05, (pop_size - 1, len(x0)))]),
        0.0, 1.0,
    )
    return sampling
