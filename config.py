"""
実行環境ごとの設定値をまとめたファイル。
このファイルの値だけ書き換えれば、他のスクリプトは変更不要です。
"""

import os

# MovieLens ml-1m データセットの配置ディレクトリ。
# https://grouplens.org/datasets/movielens/ から ml-1m をダウンロードし、
# 展開したディレクトリのパスを指定してください。
# 環境変数 MOVIELENS_DIR が設定されていればそちらを優先します。
DATA_DIR = os.environ.get("MOVIELENS_DIR", "./data/ml-1m")

TRAIN_PATH = os.path.join(DATA_DIR, "train.txt")

# 出力先ディレクトリ(図・画像の保存先)
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./outputs")

# 日本語フォント。環境に合わせて変更してください。
# 例: Mac -> "Hiragino Sans", Windows -> "Meiryo", Linux -> "Noto Sans CJK JP"
JAPANESE_FONT = os.environ.get("JAPANESE_FONT", "Hiragino Sans")

RANDOM_SEED = 42
