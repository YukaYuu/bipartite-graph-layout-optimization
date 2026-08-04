"""パレート解集合の分析: 目的間の相関、解の多様性、主成分分析。"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def analyze_pareto_front(F, objective_names, output_dir):
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
