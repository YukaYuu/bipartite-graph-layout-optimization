"""
二部グラフに対する多目的最適化に基づくレイアウト生成

概要:
    MovieLens データセット(ユーザー・映画の二部グラフ)からサブグラフを抽出し、NSGA-II を用いて、
    グラフ描画分野で広く使われる標準的な可読性指標を目的関数として同時最適化するサンプル実装です。

実行前の準備:
    1. https://grouplens.org/datasets/movielens/ から ml-1m をダウンロード
    2. 展開したディレクトリを config.py の DATA_DIR に設定
       (または環境変数 MOVIELENS_DIR で指定)
    3. pip install -r requirements.txt

実行方法:
    python bipartite_layout_optimization.py
"""

import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize

import config

try:
    mpl.rcParams["font.family"] = config.JAPANESE_FONT
except Exception:
    # 指定フォントが環境に存在しない場合はデフォルトのままにする
    pass

np.random.seed(config.RANDOM_SEED)


# ---------------------------------------------------------------------------
# データ読み込み・サブグラフ抽出
# ---------------------------------------------------------------------------

def load_movielens_graph(path):
    """MovieLens形式のデータからユーザ-映画の二部グラフを構築する"""
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
    """
    次数の高い映画からグラフ探索でサブグラフを広げ、
    さらに一番次数の高い映画周辺だけを切り出した小さいグラフを作る。

    手順:
        1. 次数の高い映画ノードを n_seed_movies 個選ぶ
        2. 各映画に接続するユーザを辿り、そのユーザが視聴した他の映画へ探索を広げる
        3. 得られたサブグラフの中で最も次数の高い映画を中心に、
           検証しやすい規模までさらに絞り込む
    """
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


# ---------------------------------------------------------------------------
# posに依存しない事前計算(エッジ端点のインデックスのみ)
# ---------------------------------------------------------------------------

def precompute_edge_structure(G):
    """座標(pos)に依存しない部分(エッジ一覧・交差判定候補ペア)を事前計算する"""
    edges = list(G.edges())
    n = len(edges)

    # ノードを共有しないエッジペアのみが交差判定の対象になる
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
    """線分 p1-p2 と p3-p4 が実際に交差しているかを判定する(端点共有は対象外)"""

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


# ---------------------------------------------------------------------------
# 標準的な可読性指標(目的関数)
# 参考: Purchase (1997) “Which Aesthetic Has the Greatest Effect on Human
# Understanding?” で挙げられているような、エッジ交差・エッジ長の均一性・
# ノードの重なり回避といった一般的なグラフ描画の美的基準。
# ---------------------------------------------------------------------------

def calc_layout_quality(pos, G, ideal_edge_length=0.15):
    """
    基本的なレイアウト品質(可読性)を評価する:
    - 繋がっているノード同士は適度な距離(ideal_edge_length)に近づける(ストレス)
    - 繋がっていないノード同士は最低限の距離を保つ(重なり防止)
    """
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
    """交差しているエッジペアの数を数え、ペア総数で正規化する"""
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
    """全エッジ長の変動係数(std/mean)。値が小さいほどエッジ長が均一"""
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


# ---------------------------------------------------------------------------
# NSGA-II問題定義(標準的な可読性指標のみを目的関数とする)
# ---------------------------------------------------------------------------

def pos_from_x(x, nodes):
    """NSGA-IIの1次元配列xをノード座標の辞書に変換"""
    coords = x.reshape(-1, 2)
    return {node: coords[i] for i, node in enumerate(nodes)}


class BipartiteLayoutProblem(Problem):
    """
    3目的の多目的最適化問題(いずれもグラフ描画分野で広く使われる標準的な指標):
    1. crossings      : エッジ交差数(正規化)
    2. layout_quality : ストレス(理想エッジ長からのズレ)+ノード重なり回避
    3. length_uniform : エッジ長の均一性(変動係数)
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


# ---------------------------------------------------------------------------
# 初期配置・サンプリング(一般的なばねモデルレイアウトを使用)
# ---------------------------------------------------------------------------

def make_sampling(pos, nodes, pop_size=50):
    """初期配置周辺にノイズを加えたNSGA-II用の初期集団を作る"""
    x0 = np.array([[pos[node][0], pos[node][1]] for node in nodes]).flatten()
    sampling = np.clip(
        np.vstack([x0, x0 + np.random.normal(0, 0.05, (pop_size - 1, len(x0)))]),
        0.0, 1.0,
    )
    return sampling


def draw_layout(graph, pos, ax, title=None):
    node_colors = ["blue" if n.startswith("u_") else "red" for n in graph.nodes()]
    nx.draw(graph, pos, node_color=node_colors, node_size=50,
            with_labels=False, ax=ax)
    if title:
        ax.set_title(title)


# ---------------------------------------------------------------------------
# パレート解の分析(相関・多様性・PCA)
# 一般的な多目的最適化の結果分析手法であり、二部グラフに特有の手法ではない。
# ---------------------------------------------------------------------------

def analyze_pareto_front(F, objective_names, output_dir):
    """
    パレート解集合Fに対して以下を行う:
    - 目的関数間のピアソン/スピアマン相関のヒートマップ
    - 正規化後のパレート解間距離分布
    - 主成分分析による実質的な次元数の確認
    """
    import seaborn as sns
    from scipy.spatial.distance import pdist
    from sklearn.decomposition import PCA

    df_F = pd.DataFrame(F, columns=objective_names)

    pearson_corr = df_F.corr(method="pearson")
    spearman_corr = df_F.corr(method="spearman")
    print("=== Pearson相関 ===")
    print(pearson_corr.round(3))
    print("\n=== Spearman相関 ===")
    print(spearman_corr.round(3))

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    sns.heatmap(pearson_corr, annot=True, fmt=".2f", cmap="coolwarm",
                vmin=-1, vmax=1, ax=axes[0], square=True)
    axes[0].set_title("Pearson相関")
    sns.heatmap(spearman_corr, annot=True, fmt=".2f", cmap="coolwarm",
                vmin=-1, vmax=1, ax=axes[1], square=True)
    axes[1].set_title("Spearman相関")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "objective_correlation.png"), dpi=120)
    plt.close(fig)

    print("\n=== 各目的の統計量(正規化前) ===")
    print(df_F.describe().round(4))

    F_norm = (F - F.min(axis=0)) / (F.max(axis=0) - F.min(axis=0) + 1e-9)
    pairwise_dists = pdist(F_norm, metric="euclidean")
    print("\n=== パレート解間の距離(正規化後) ===")
    print(f"平均距離: {pairwise_dists.mean():.4f}")
    print(f"最小距離: {pairwise_dists.min():.4f}")
    print(f"最大距離: {pairwise_dists.max():.4f}")

    plt.figure(figsize=(6, 4))
    plt.hist(pairwise_dists, bins=30)
    plt.xlabel("正規化後ユークリッド距離")
    plt.ylabel("頻度")
    plt.title("パレート解間の距離分布(多様性)")
    plt.savefig(os.path.join(output_dir, "pareto_diversity_histogram.png"), dpi=120)
    plt.close()

    pca = PCA()
    pca.fit(F_norm)
    print("\n=== 主成分分析(累積寄与率) ===")
    cum_var = np.cumsum(pca.explained_variance_ratio_)
    for i, (var, cum) in enumerate(zip(pca.explained_variance_ratio_, cum_var)):
        print(f"PC{i + 1}: 寄与率={var:.3f}, 累積寄与率={cum:.3f}")

    plt.figure(figsize=(6, 4))
    plt.plot(range(1, len(cum_var) + 1), cum_var, marker="o")
    plt.axhline(0.9, color="red", linestyle="--", label="90%ライン")
    plt.xlabel("主成分数")
    plt.ylabel("累積寄与率")
    plt.title("目的空間の実質的な次元数")
    plt.legend()
    plt.savefig(os.path.join(output_dir, "objective_pca.png"), dpi=120)
    plt.close()


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------

def main():
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

    # 3. パレート解から代表解を1つ選んで可視化(暫定: 正規化後の合計スコアが最小の解)
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
