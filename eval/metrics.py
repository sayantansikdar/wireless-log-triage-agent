import math

def recall_at_k(retrieved_ids: list[str], gold_ids: set[str], k: int) -> float:
    """
    Calculate Recall@k for a single query.
    Returns 1.0 if at least one gold ID is in the top k retrieved IDs, 0.0 otherwise.
    """
    top_k = retrieved_ids[:k]
    for doc_id in top_k:
        if doc_id in gold_ids:
            return 1.0
    return 0.0

def mrr_at_k(retrieved_ids: list[str], gold_ids: set[str], k: int) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR@k) for a single query.
    Returns 1/rank of the first relevant document in the top k, or 0.0.
    """
    top_k = retrieved_ids[:k]
    for i, doc_id in enumerate(top_k):
        if doc_id in gold_ids:
            return 1.0 / (i + 1)
    return 0.0

def ndcg_at_k(retrieved_ids: list[str], gold_ids: set[str], k: int) -> float:
    """
    Calculate nDCG@k for a single query.
    Binary relevance: relevance is 1 if in gold_ids, 0 otherwise.
    """
    top_k = retrieved_ids[:k]
    dcg = 0.0
    for i, doc_id in enumerate(top_k):
        if doc_id in gold_ids:
            # log2(i+2) because our ranks are 0-indexed (i=0 is rank 1, so log2(2) = 1)
            dcg += 1.0 / math.log2(i + 2)
            
    # Calculate IDCG (Ideal DCG)
    idcg = 0.0
    # The max possible relevant items is the min of k and number of gold ids
    max_relevant = min(k, len(gold_ids))
    for i in range(max_relevant):
        idcg += 1.0 / math.log2(i + 2)
        
    if idcg == 0.0:
        return 0.0
        
    return dcg / idcg
