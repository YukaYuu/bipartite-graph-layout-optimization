# 二部グラフに対する多目的最適化に基づくレイアウト生成(サンプル実装)

グラフ描画の可読性を評価する複数の指標は互いにトレードオフの関係にあることが知られています。本リポジトリは、NSGA-II を用いた多目的最適化によって、二部グラフに対して複数のレイアウト候補(パレート解)を同時に生成する手法のサンプル実装です。

※研究で提案する予定の評価指標・目的関数については、研究成果保護の観点から本リポジトリでは公開対象外としています。
本リポジトリでは比較対象となる一般的な可読性指標を用いた最適化部分のみを公開しています。

## 本リポジトリに含まれる内容

- MovieLens データセットからのユーザー・映画二部グラフの構築とサブグラフ抽出
- NSGA-II による多目的最適化のセットアップ(pymoo使用)
- グラフ描画分野で広く使われる標準的な可読性指標
  - エッジ交差数
  - ストレス(理想エッジ長からのズレ)とノードの重なり回避
  - エッジ長の均一性
- 得られたパレート解集合に対する相関分析(ピアソン・スピアマン)、解の多様性(距離分布)分析、主成分分析(PCA)

## ディレクトリ構成

```
.
├── bipartite_layout_optimization.py  # メインスクリプト
├── config.py                          # パス・パラメータ設定
├── requirements.txt
└── README.md
```

## 実行方法

### 1. データセットの準備

[MovieLens ml-1m](https://grouplens.org/datasets/movielens/) をダウンロードし、
`train.txt`(各行が `ユーザーID 映画ID1 映画ID2 ...` の形式のファイル)を
任意のディレクトリに配置してください。

### 2. 環境構築

```bash
pip install -r requirements.txt
```

### 3. データセットのパス指定

`config.py` の `DATA_DIR` を書き換えるか、環境変数で指定します。

```bash
export MOVIELENS_DIR=/path/to/ml-1m
```

### 4. 実行

```bash
python bipartite_layout_optimization.py
```

`outputs/` ディレクトリに、最適化後のレイアウト画像や、パレート解の相関分析・
多様性分析・PCAの図が出力されます。

## 参考

- Purchase, H. C. (1997). Which aesthetic has the greatest effect on human understanding?
- MovieLens Dataset: https://grouplens.org/datasets/movielens/
- pymoo (多目的最適化ライブラリ): https://pymoo.org/
