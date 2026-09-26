def reciprocal_rank_fusion(dense_results: list, sparse_results: list, k: int = 60) -> list:
    """
    Fuses two lists of retrieval results using Reciprocal Rank Fusion (RRF).
    score = 1 / (k + rank)
    We expect dense_results and sparse_results to be lists of dicts with an "id" or "chunk_id" field.
    """
    rrf_scores = {}
    
    # Map for quick lookup of the actual document payload
    doc_map = {}
    
    def add_to_scores(results_list):
        for rank, doc in enumerate(results_list):
            doc_id = doc.get("chunk_id", str(id(doc)))
            if doc_id not in doc_map:
                doc_map[doc_id] = doc
                
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0
                
            rrf_scores[doc_id] += 1.0 / (k + rank + 1)
            
    add_to_scores(dense_results)
    add_to_scores(sparse_results)
    
    # Sort by RRF score descending
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    
    # Return fused results
    fused = []
    for doc_id in sorted_ids:
        doc = dict(doc_map[doc_id])
        doc["rrf_score"] = rrf_scores[doc_id]
        fused.append(doc)
        
    return fused

def alpha_weighting(dense_results: list, sparse_results: list, alpha: float = 0.5) -> list:
    """
    Linear combination of normalized scores: score = alpha * dense_score + (1 - alpha) * sparse_score.
    Requires score normalization if the spaces are different (e.g. cosine vs BM25).
    For simplicity, we use min-max normalization per list.
    """
    def normalize(results):
        if not results: return []
        scores = [d.get("score", 0.0) for d in results]
        min_s, max_s = min(scores), max(scores)
        if max_s == min_s:
            for d in results:
                d["norm_score"] = 1.0
        else:
            for d in results:
                d["norm_score"] = (d.get("score", 0.0) - min_s) / (max_s - min_s)
        return results

    dense = normalize(dense_results)
    sparse = normalize(sparse_results)
    
    combined_scores = {}
    doc_map = {}
    
    for doc in dense:
        doc_id = doc.get("chunk_id", str(id(doc)))
        doc_map[doc_id] = doc
        combined_scores[doc_id] = combined_scores.get(doc_id, 0.0) + (alpha * doc["norm_score"])
        
    for doc in sparse:
        doc_id = doc.get("chunk_id", str(id(doc)))
        doc_map[doc_id] = doc
        combined_scores[doc_id] = combined_scores.get(doc_id, 0.0) + ((1.0 - alpha) * doc["norm_score"])
        
    sorted_ids = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
    
    fused = []
    for doc_id in sorted_ids:
        doc = dict(doc_map[doc_id])
        doc["fused_score"] = combined_scores[doc_id]
        fused.append(doc)
        
    return fused
