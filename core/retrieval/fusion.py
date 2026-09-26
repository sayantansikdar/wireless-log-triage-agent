import logging
from typing import List, Dict, Any
from core.retrieval.exact import extract_exact_tokens, build_lancedb_filter
from core.retrieval.hybrid import reciprocal_rank_fusion

logger = logging.getLogger(__name__)

def retrieve_fused(
    vector_store,
    embedding_func,
    query: str,
    k: int = 10,
    dense_weight: float = 1.0,
    sparse_weight: float = 1.0,
    use_exact_filter: bool = True
) -> List[Dict[str, Any]]:
    """
    Executes a complete retrieval pipeline:
    1. Exact pre-filtering based on telecom tokens
    2. Hybrid (Dense + BM25) search using LanceDB or custom RRF
    """
    # If the vector store natively supports hybrid search via Tantivy:
    # return vector_store.search(query, query_type="hybrid").limit(k).to_list()
    
    # However, since we are doing custom RRF and filtering, we'll demonstrate the logic:
    
    pre_filter = ""
    if use_exact_filter:
        tokens = extract_exact_tokens(query)
        if tokens:
            pre_filter = build_lancedb_filter(tokens)
            logger.info(f"Extracted tokens: {tokens}. Using pre-filter: {pre_filter}")
            
    # Compute query embedding for dense search
    query_embedding = embedding_func.compute_query_embeddings(query)[0]
    
    # Dense Search
    dense_search = vector_store.search(query_embedding).limit(k*2)
    if pre_filter:
        dense_search = dense_search.where(pre_filter)
    dense_results = dense_search.to_list()
    
    # BM25 Sparse Search (requires FTS index on vector_store)
    try:
        sparse_search = vector_store.search(query, query_type="fts").limit(k*2)
        if pre_filter:
            sparse_search = sparse_search.where(pre_filter)
        sparse_results = sparse_search.to_list()
    except Exception as e:
        logger.warning(f"FTS search failed (index missing?): {e}. Falling back to dense only.")
        sparse_results = []
        
    # Fuse
    if not sparse_results:
        fused = dense_results
    else:
        fused = reciprocal_rank_fusion(dense_results, sparse_results, k=60)
        
    return fused[:k]
