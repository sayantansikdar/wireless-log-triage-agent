# Wireless Log Triage Agent

An Agentic RAG system designed for Apple's Wireless Technology & Ecosystems (WTE) teams. It ingests massive 3GPP and IEEE 802.11 specifications and acts as an expert assistant to triage failure snippets from wireless logs (e.g., Attach Rejects, Wi-Fi Auth Timeouts).

This project was built as an extension of a base local-LLM-RAG pipeline to demonstrate domain-specific innovations in retrieval and data privacy.

## Key Innovations

1. **Structure-Aware Ingestion:** Replaces naive chunking with ATX heading parsing, ensuring 3GPP tables remain intact and injecting exact `[Spec, Section, Title]` metadata into every chunk.
2. **Deterministic Exact ID Pre-filtering:** Intercepts out-of-vocabulary telecom tokens (like `T3410` or `#15`) and forces them into candidate pools, solving the dense embedding mismatch problem.
3. **Hybrid Retrieval (RRF):** Fuses Dense embeddings (Semantic) with BM25 (Lexical) using Reciprocal Rank Fusion, creating a robust retrieval pipeline.
4. **Keyed-HMAC Pseudonymization:** Safely redacts PII (MAC, IMSI, IMEI) from logs *before* they hit the LLM using a keyed HMAC (e.g., `MAC_a1b2`). This preserves unique entities for failure correlation without leaking raw data. It features Luhn checksum validation to prevent false-positive redaction of timers and counters.
5. **Deterministic Retrieval Evaluation:** Evaluates retrieval natively at the *section* level (Recall@k, MRR) rather than the volatile *chunk* level.

## Getting Started

### 1. Install Dependencies
```bash
uv sync --python 3.13
```

### 2. Start Local LLM
Ensure [Ollama](https://ollama.com/) is running locally with the required models:
```bash
ollama pull mistral
ollama pull nomic-embed-text
```

### 3. Fetch the Corpus & Build Index
Download the exact 3GPP specs and build the LanceDB vector index:
```bash
uv run core/ingest/fetch_corpus.py
uv run python -m core.ingest.baseline_index
```

### 4. Run Triage
Pass a raw log snippet to the agent:
```bash
uv run scripts/triage.py --log "14:32:01.450 [NAS] Rx ATTACH REJECT (EMM Cause: 15)"
```
The agent will redact PII, output an audit report, search the 3GPP specs, and provide a diagnostic summary.

## Project Structure
- `core/ingest/`: 3GPP spec downloading, parsing, structure-aware chunking.
- `core/retrieval/`: Exact pre-filtering, BM25/Dense fusion (RRF).
- `core/redact/`: MAC/IMSI/IMEI detectors, HMAC pseudonymizer.
- `core/agent.py`: Pydantic AI agent wiring.
- `eval/`: Retrieval metrics (Recall, MRR) and Golden Sets.
- `scenarios/`: Markdown definitions of real-world log failure patterns.

## Evaluation
Run pure retrieval evaluation:
```bash
uv run python eval/retrieval_eval.py
```
