import json
import logging
import time
from pathlib import Path

# Fix path to allow importing from core
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document_loader import get_embedding_function, DEFAULT_EMBEDDING_MODEL
from core.agent import _create_vector_store
from eval.metrics import recall_at_k, mrr_at_k, ndcg_at_k

logger = logging.getLogger(__name__)

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

def load_golden_set(split: str = "test") -> list[dict]:
    path = Path(f"eval/golden/{split}.jsonl")
    if not path.exists():
        return []
    with open(path, "r") as f:
        return [json.loads(line) for line in f]

def heuristic_extract_section(text: str) -> str:
    """
    Attempt to extract a section number from naive chunk text.
    This is a temporary heuristic for the baseline since naive chunks lack metadata.
    We just look for section-like strings (e.g. '5.5.1.2.5').
    """
    import re
    # Look for patterns like "5.5.1.2.5" 
    matches = re.findall(r'\b\d+\.\d+(?:\.\d+)*\b', text)
    return matches if matches else ["UNKNOWN"]

def run_eval(split: str = "test", k: int = 10, run_name: str = "baseline_dense"):
    logger.info(f"Starting {run_name} eval on {split} split...")
    golden_data = load_golden_set(split)
    
    if not golden_data:
        logger.warning(f"No golden data found for {split} split.")
        return

    # Initialize LanceDB table and embedding function
    vector_store = _create_vector_store(DEFAULT_EMBEDDING_MODEL, reload=False)
    embedding_func = get_embedding_function(DEFAULT_EMBEDDING_MODEL)
    
    results = {
        "config": {
            "model": DEFAULT_EMBEDDING_MODEL,
            "k": k,
            "split": split,
            "run_name": run_name
        },
        "aggregate_metrics": {
            "Recall@10": 0.0,
            "MRR@10": 0.0,
            "nDCG@10": 0.0,
            "latency_p50": 0.0,
            "latency_p95": 0.0
        },
        "per_question": []
    }
    
    latencies = []
    recall_sum = 0.0
    mrr_sum = 0.0
    ndcg_sum = 0.0
    
    for item in golden_data:
        question = item["question"]
        gold_sections = {g["section"] for g in item["gold_sections"]}
        
        start_time = time.time()
        # Query
        query_embedding = embedding_func.compute_query_embeddings(question)[0]
        db_results = vector_store.search(query_embedding).limit(k).to_list()
        latency = time.time() - start_time
        latencies.append(latency)
        
        # Extract section numbers using heuristic since baseline lacks metadata
        retrieved_sections = []
        for doc in db_results:
            text = doc.get("text", "")
            found_sections = heuristic_extract_section(text)
            retrieved_sections.extend(found_sections)
            
        r_k = recall_at_k(retrieved_sections, gold_sections, k)
        m_k = mrr_at_k(retrieved_sections, gold_sections, k)
        n_k = ndcg_at_k(retrieved_sections, gold_sections, k)
        
        recall_sum += r_k
        mrr_sum += m_k
        ndcg_sum += n_k
        
        results["per_question"].append({
            "id": item["id"],
            "recall": r_k,
            "mrr": m_k,
            "ndcg": n_k,
            "latency": latency,
            "retrieved_sections": retrieved_sections[:k]
        })
        
    n = len(golden_data)
    latencies.sort()
    p50 = latencies[int(n * 0.5)] if n > 0 else 0
    p95 = latencies[int(n * 0.95)] if n > 0 else 0
    
    results["aggregate_metrics"]["Recall@10"] = recall_sum / n if n > 0 else 0
    results["aggregate_metrics"]["MRR@10"] = mrr_sum / n if n > 0 else 0
    results["aggregate_metrics"]["nDCG@10"] = ndcg_sum / n if n > 0 else 0
    results["aggregate_metrics"]["latency_p50"] = p50
    results["aggregate_metrics"]["latency_p95"] = p95
    
    output_path = RESULTS_DIR / f"{run_name}.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Eval complete. Results saved to {output_path}")
    logger.info(f"Recall@10: {results['aggregate_metrics']['Recall@10']:.4f}")
    logger.info(f"MRR@10: {results['aggregate_metrics']['MRR@10']:.4f}")
    logger.info(f"nDCG@10: {results['aggregate_metrics']['nDCG@10']:.4f}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    run_eval()
