from rag_eval.metrics import (
    compute_retrieval_metrics,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_precision_at_k_all_relevant():
    assert precision_at_k(["a", "b", "c"], {"a", "b", "c"}, 3) == 1.0


def test_precision_at_k_none_relevant():
    assert precision_at_k(["a", "b", "c"], {"x", "y"}, 3) == 0.0


def test_precision_at_k_partial():
    assert precision_at_k(["a", "b", "c", "d"], {"a", "c"}, 4) == 0.5


def test_precision_at_k_truncates_to_k():
    # Only the first k=2 are considered, even though a relevant doc is at rank 3.
    assert precision_at_k(["a", "b", "c"], {"c"}, 2) == 0.0


def test_precision_at_k_empty_retrieved():
    assert precision_at_k([], {"a"}, 5) == 0.0


def test_recall_at_k_all_found():
    assert recall_at_k(["a", "b", "c"], {"a", "b"}, 3) == 1.0


def test_recall_at_k_partial():
    assert recall_at_k(["a", "x", "y"], {"a", "b"}, 3) == 0.5


def test_recall_at_k_no_relevant_labels():
    # Trap questions with no gold-relevant chunks: recall is defined as 0.
    assert recall_at_k(["a", "b"], set(), 5) == 0.0


def test_recall_at_k_relevant_beyond_k():
    assert recall_at_k(["a", "b", "c"], {"c"}, 2) == 0.0


def test_mrr_first_position():
    assert mrr(["a", "b", "c"], {"a"}) == 1.0


def test_mrr_third_position():
    assert mrr(["x", "y", "a"], {"a"}) == 1.0 / 3


def test_mrr_not_found():
    assert mrr(["x", "y", "z"], {"a"}) == 0.0


def test_mrr_uses_first_relevant_hit():
    # "a" is relevant and appears first at rank 2; a later relevant "b" doesn't matter.
    assert mrr(["x", "a", "b"], {"a", "b"}) == 0.5


def test_ndcg_at_k_perfect_ranking():
    # All relevant chunks at the top → NDCG == 1.0
    assert ndcg_at_k(["a", "b", "x"], {"a", "b"}, 3) == 1.0


def test_ndcg_at_k_worst_ranking():
    assert ndcg_at_k(["x", "y", "z"], {"a"}, 3) == 0.0


def test_ndcg_at_k_partial_credit_for_order():
    # Relevant chunk "a" is ranked below irrelevant "x" — should be > 0 but < 1.
    score = ndcg_at_k(["x", "a"], {"a", "b"}, 2)
    assert 0.0 < score < 1.0


def test_ndcg_at_k_no_relevant_labels():
    assert ndcg_at_k(["a", "b"], set(), 5) == 0.0


def test_ndcg_at_k_order_sensitivity():
    # Same relevant set, different order — better order should score higher.
    better = ndcg_at_k(["a", "b", "x"], {"a", "b"}, 3)
    worse = ndcg_at_k(["x", "a", "b"], {"a", "b"}, 3)
    assert better > worse


def test_compute_retrieval_metrics_shape():
    metrics = compute_retrieval_metrics(["a", "x", "b"], {"a", "b"}, ks=(1, 2, 3))
    assert set(metrics.precision_at_k) == {1, 2, 3}
    assert set(metrics.recall_at_k) == {1, 2, 3}
    assert set(metrics.ndcg_at_k) == {1, 2, 3}
    assert metrics.mrr == 1.0
    assert metrics.recall_at_k[3] == 1.0
    assert metrics.precision_at_k[1] == 1.0
