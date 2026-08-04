import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize

from bipartite_pareto_layout import config
from bipartite_pareto_layout.analysis import analyze_pareto_front
from bipartite_pareto_layout.data import build_small_subgraph, load_movielens_graph
from bipartite_pareto_layout.geometry import pos_from_x
from bipartite_pareto_layout.plotting import draw_layout
from bipartite_pareto_layout.problem import BipartiteLayoutProblem, make_sampling


def main():
    np.random.seed(config.RANDOM_SEED)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # 1. データ読み込み・サブグラフ抽出
    M = load_movielens_graph(config.TRAIN_PATH)
    small_graph = build_small_subgraph(M)
    print(f"ノード数: {small_graph.number_of_nodes()}")
    print(f"エッジ数: {small_graph.number_of_edges()}")

    # 2. 初期配置(一般的なばねモデルレイアウト)とNSGA-IIの実行
    nodes = list(small_graph.nodes())
    pos_spring = nx.spring_layout(small_graph, seed=config.RANDOM_SEED)
    sampling = make_sampling(pos_spring, nodes)

    problem = BipartiteLayoutProblem(small_graph)
    algorithm = NSGA2(pop_size=100, sampling=sampling, seed=config.RANDOM_SEED)
    res = minimize(problem, algorithm, termination=("n_gen", 1000), verbose=True)
    print(f"パレート解の数: {len(res.F)}")

    # 3. パレート解から代表解を1つ選んで可視化
    F = res.F
    F_norm = (F - F.min(axis=0)) / (F.max(axis=0) - F.min(axis=0) + 1e-9)
    best_idx = np.argmin(F_norm.sum(axis=1))
    pos_best = pos_from_x(res.X[best_idx], nodes)

    fig, ax = plt.subplots(figsize=(6, 6))
    draw_layout(small_graph, pos_best, ax,
                title="NSGA-II Optimized Layout (crossings / stress / length uniformity)")
    plt.savefig(os.path.join(config.OUTPUT_DIR, "optimized_layout.png"), dpi=120)
    plt.close(fig)

    # 4. パレート解集合の分析(相関・多様性・PCA)
    objective_names = ["crossings", "layout_quality", "length_uniform"]
    analyze_pareto_front(F, objective_names, config.OUTPUT_DIR)


if __name__ == "__main__":
    main()
