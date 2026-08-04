import numpy as np

from bipartite_pareto_layout.problem import BipartiteLayoutProblem, make_sampling


def test_bipartite_layout_problem_evaluates_batch_of_candidates(small_bipartite_graph):
    G = small_bipartite_graph
    problem = BipartiteLayoutProblem(G)
    assert problem.n_var == G.number_of_nodes() * 2
    assert problem.n_obj == 3

    rng = np.random.default_rng(0)
    X = rng.uniform(0, 1, size=(4, problem.n_var))
    out = {}
    problem._evaluate(X, out)

    F = out["F"]
    assert F.shape == (4, 3)
    assert np.all(np.isfinite(F))
    assert np.all(F >= 0)  # 交差率・レイアウト品質・エッジ長均一性はいずれも非負


def test_make_sampling_first_row_is_unperturbed_initial_position(small_bipartite_graph):
    G = small_bipartite_graph
    nodes = list(G.nodes())
    pos = {n: np.array([0.3, 0.7]) for n in nodes}
    sampling = make_sampling(pos, nodes, pop_size=10)
    x0 = np.array([pos[n] for n in nodes]).flatten()
    assert np.allclose(sampling[0], x0)
    assert sampling.shape == (10, len(nodes) * 2)
    assert np.all(sampling >= 0.0) and np.all(sampling <= 1.0)
