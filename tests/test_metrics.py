import math
from eval.metrics import recall_at_k, mrr_at_k, ndcg_at_k

def test_recall_at_k():
    gold = {"sec1", "sec2"}
    # Gold at rank 1
    assert recall_at_k(["sec1", "sec3", "sec4"], gold, 2) == 1.0
    # Gold at rank 2
    assert recall_at_k(["sec3", "sec2", "sec4"], gold, 2) == 1.0
    # Gold at rank 3 (outside top 2)
    assert recall_at_k(["sec3", "sec4", "sec2"], gold, 2) == 0.0
    # No gold
    assert recall_at_k(["sec3", "sec4"], gold, 2) == 0.0

def test_mrr_at_k():
    gold = {"sec1", "sec2"}
    # Gold at rank 1
    assert mrr_at_k(["sec1", "sec3", "sec4"], gold, 3) == 1.0
    # Gold at rank 2
    assert mrr_at_k(["sec3", "sec2", "sec4"], gold, 3) == 0.5
    # Gold at rank 3
    assert mrr_at_k(["sec3", "sec4", "sec1"], gold, 3) == 1/3
    # Outside k
    assert mrr_at_k(["sec3", "sec4", "sec1"], gold, 2) == 0.0

def test_ndcg_at_k():
    gold = {"sec1", "sec2"}
    
    # Perfect ranking: both gold items at rank 1 and 2
    # DCG = 1/log2(2) + 1/log2(3) = 1 + 0.6309 = 1.6309
    # IDCG = 1.6309
    assert math.isclose(ndcg_at_k(["sec1", "sec2", "sec3"], gold, 3), 1.0)
    
    # One relevant item at rank 2
    # DCG = 0 + 1/log2(3) = 0.6309
    # IDCG (2 gold items) = 1/log2(2) + 1/log2(3) = 1.6309
    dcg = 1.0 / math.log2(3)
    idcg = 1.0 + 1.0 / math.log2(3)
    assert math.isclose(ndcg_at_k(["sec3", "sec2", "sec4"], gold, 3), dcg / idcg)
    
    # No relevant items
    assert ndcg_at_k(["sec3", "sec4", "sec5"], gold, 3) == 0.0
