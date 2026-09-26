from core.retrieval.exact import extract_exact_tokens, build_lancedb_filter
from core.retrieval.hybrid import reciprocal_rank_fusion, alpha_weighting

def test_exact_token_extraction():
    q = "Attach rejected with cause 15 and timer T3410 expired."
    tokens = extract_exact_tokens(q)
    assert "T3410" in tokens
    assert "#15" in tokens
    
    q2 = "Look at section 5.5.1.2.5"
    tokens2 = extract_exact_tokens(q2)
    assert "5.5.1.2.5" in tokens2

def test_build_filter():
    tokens = ["T3410", "5.5.1.2.5", "#15"]
    f = build_lancedb_filter(tokens)
    assert "text LIKE '%T3410%'" in f
    assert "section = '5.5.1.2.5'" in f
    assert "text LIKE '%#15%'" in f
    assert " OR " in f

def test_rrf():
    dense = [
        {"chunk_id": "a"},
        {"chunk_id": "b"},
        {"chunk_id": "c"},
    ]
    sparse = [
        {"chunk_id": "b"},
        {"chunk_id": "c"},
        {"chunk_id": "d"},
    ]
    
    fused = reciprocal_rank_fusion(dense, sparse, k=1)
    
    # score(a) = 1/(1+0+1) = 0.5
    # score(b) = 1/(1+1+1) + 1/(1+0+1) = 1/3 + 1/2 = 0.833
    # score(c) = 1/(1+2+1) + 1/(1+1+1) = 1/4 + 1/3 = 0.583
    # score(d) = 1/(1+2+1) = 0.25
    # order: b, c, a, d
    assert fused[0]["chunk_id"] == "b"
    assert fused[1]["chunk_id"] == "c"
    assert fused[2]["chunk_id"] == "a"
    assert fused[3]["chunk_id"] == "d"
