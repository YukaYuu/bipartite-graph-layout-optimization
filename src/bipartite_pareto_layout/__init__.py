import matplotlib as mpl

from bipartite_pareto_layout import config

try:
    mpl.rcParams["font.family"] = config.JAPANESE_FONT
except Exception:
    # 指定フォントが環境に存在しない場合はデフォルトのままにする
    pass

__version__ = "0.1.0"
