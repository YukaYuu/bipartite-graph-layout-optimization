"""レイアウトの描画。"""

import networkx as nx


def draw_layout(graph, pos, ax, title=None):
    node_colors = ["blue" if n.startswith("u_") else "red" for n in graph.nodes()]
    nx.draw(graph, pos, node_color=node_colors, node_size=50,
            with_labels=False, ax=ax)
    if title:
        ax.set_title(title)
