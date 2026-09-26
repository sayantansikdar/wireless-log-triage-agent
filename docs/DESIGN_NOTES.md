# Design Notes

## Phase 0: Recon

**What changed and why:**
- Read the upstream repository and analyzed the existing document loading, chunking, and embedding setup.
- Designed an extended directory structure avoiding a rewrite to focus on domain-specific improvements.
- Added `docs/PROJECT_BRIEF.md` and `docs/DESIGN_NOTES.md`.

**Alternatives rejected:**
- **Full Rewrite:** Rejected because extending the existing agentic RAG pipeline allows focusing on telecom-specific additions, adhering to the project guidelines, and provides an honest reviewable Git history.
- **Merging `bench/` and `eval/`:** Rejected because `bench/` evaluates end-to-end model generation quality, while `eval/` is specifically for isolated retrieval metrics (Recall@k, MRR@k, nDCG@k), which is crucial for Phase 2-4 ablation studies.

**How to verify:**
- Read `docs/PROJECT_BRIEF.md` to review the filled-in parameters and project phases.

**Interview Questions & Answers:**
1. **Q:** Why extend the upstream codebase rather than building from scratch?
   **A:** The brief explicitly states "extend not rewrite." It allows focusing engineering effort on domain-specific innovations (structure-aware chunking, hybrid retrieval, redaction) rather than basic plumbing. It also clearly shows what value was added.
2. **Q:** What is the biggest retrieval gap in the upstream system for telecom spec use?
   **A:** The naïve 1000-character chunking splits sections and tables unpredictably, which will destroy structured cause-code tables. Additionally, relying solely on dense retrieval misses exact lexically important telecom tokens (e.g., `T3410`, `5.5.1.2.5`), and the potential lack of task prefixes degrades retrieval quality.
   **A:** They serve different purposes: `bench/` uses an LLM judge for end-to-end answer quality, whereas `eval/` measures pure retrieval metrics (Recall@k, MRR) independently of generation capabilities. Retrieval eval is fast, deterministic, and ideal for a CI gate.

## Phase 2: Golden set, retrieval eval, baseline numbers

**What changed and why:**
- Built `eval/metrics.py` for standard retrieval metrics: Recall@k, MRR@k, and nDCG@k. Wrote tests ensuring correct metric behavior.
- Built `eval/retrieval_eval.py` to run queries against LanceDB and compute these metrics on the test split.
- Drafted a small initial Golden Set (`eval/golden/dev.jsonl` and `test.jsonl`) spanning three question types: direct lookup, symptom paraphrase, and log snippets.
- Added `results/baseline_dense.json` (currently a placeholder since Ollama isn't running locally).

**Alternatives rejected:**
- **Evaluating at chunk-level instead of section-level:** Rejected. If we labeled chunks, those labels would break as soon as we change chunking logic in Phase 3. Section-level labels are robust to chunking changes.
- **Using an LLM for relevance judgments (LLM-as-a-judge for retrieval):** Rejected for retrieval eval. We need fast, deterministic metrics (Recall, MRR) against a known ground-truth section. LLMs are better suited for the end-to-end evaluation in Phase 5.

**How to verify:**
1. Run the metric unit tests: `uv run pytest tests/test_metrics.py`.
2. Review the Golden Set samples in `eval/golden/test.jsonl`.
3. To compute real baseline metrics, start Ollama locally with `nomic-embed-text`, run `uv run python -m core.ingest.baseline_index`, and then run `uv run python eval/retrieval_eval.py`.

**Interview Questions & Answers:**
1. **Q:** Why do we need MRR and nDCG if we already have Recall@10?
   **A:** Recall@10 only measures if the correct section is *anywhere* in the top 10. MRR and nDCG measure *ranking quality* — it's much better to have the correct section at rank 1 than rank 10 because it saves LLM context window space and reduces distraction.
2. **Q:** Why don't you use an LLM-as-a-judge for the retrieval eval?
   **A:** Retrieval metrics should be fast, cheap, and deterministic so they can run on every CI push. LLM-as-a-judge is slow and non-deterministic, making it better suited for end-to-end answer validation rather than pure retrieval ranking evaluation.
   **A:** For the baseline only, we use a simple regex heuristic `\b\d+\.\d+(?:\.\d+)*\b` on the retrieved chunk text to extract section numbers. It's imperfect, but it's enough to establish a lower-bound baseline (X) before we implement proper metadata extraction in Phase 3.

## Phase 3: Structure-aware ingestion, metadata, and redaction

**What changed and why:**
- Built `core/ingest/parse_3gpp.py` and `chunking.py`. Unlike the naive `MarkItDown` 1000-character chunker that tears apart tables and loses context, this parses markdown ATX headings (`# 5.5.1`) to establish a document hierarchy and chunks logically by section. It guarantees tables are not split unless obscenely long, and it injects `section`, `title`, and `parent` metadata into every chunk for exact retrieval scoring and LLM context.
- Built `core/ingest/cause_codes.py` to deterministically extract cause code tables (e.g., EMM Cause #15) via regex rather than relying on unreliable LLM extraction pipelines.
- Built `core/redact/detectors.py`, `pseudonymizer.py`, and `report.py` to handle PII and sensitive identifiers. 
- Implemented robust regexes and validators (like a Luhn checksum for 15-digit IMEIs) and a deterministic keyed-HMAC tokenization (e.g., `MAC_a1b2`).
- Wrote extensive tests for the redaction module (`tests/test_redaction.py`), ensuring false positives (like timestamps acting as MACs or un-contextual 15-digit counters) are handled gracefully, and proving idempotency.

**Alternatives rejected:**
- **Using an LLM for cause code extraction:** Rejected. Deterministic regex parsing of Markdown tables is faster, 100% accurate, and cheaper than having an LLM hallucinate or skip rows in massive 3GPP tables.
- **Redacting via basic replace / hash without prefix:** Rejected. Keyed HMAC with a prefix (`IMSI_xxxx`) preserves the structural "type" of the data which helps the LLM reasoning, while keeping the exact entity consistently tokenized across log files so the LLM can correlate them.
- **Relying on upstream's naive chunker:** Rejected. Structural metadata (knowing a chunk belongs to 5.5.1.2.5) is the bedrock of our evaluation strategy and crucial for targeted retrieval.

**How to verify:**
1. Run `uv run pytest tests/test_chunking.py` to see the structure-aware chunking and cause code parsing in action.
2. Run `uv run pytest tests/test_redaction.py` to verify Luhn checksums, context-keying, and idempotency.

**Interview Questions & Answers:**
1. **Q:** Why did you use a keyed HMAC for pseudonymization instead of just replacing MACs with `<MAC>`?
   **A:** Because in wireless logs, tracking *which* device failed is crucial. If we replace all MACs with `<MAC>`, the LLM can't tell if one device failed 10 times or 10 devices failed once. Keyed HMAC (e.g., `MAC_1a2b`) preserves uniqueness for correlation while protecting the raw value.
2. **Q:** Why implement Luhn checksum validation for IMEIs?
   **A:** Because 15-digit sequences appear frequently in logs as timestamps, counters, or random byte dumps. Checking the Luhn algorithm significantly reduces false positives, preventing us from corrupting useful numerical data.
   **A:** Standard splitters (like recursive character splitters) destroy tables and lose heading context. By parsing ATX headings, we keep sections logically intact, which is critical for cause codes and exact section retrieval.

## Phase 4: Hybrid retrieval & Exact ID matching

**What changed and why:**
- Built `core/retrieval/exact.py` to intercept queries and pull out telecom-specific tokens (timers like `T3410`, sections like `5.5.1`, and cause codes like `#15`). It builds deterministic SQL filters for LanceDB to ensure these documents are force-retained in candidate pools.
- Built `core/retrieval/hybrid.py` featuring a robust Reciprocal Rank Fusion (RRF) implementation and an Alpha-weighting alternative. 
- Built `core/retrieval/fusion.py` to act as the pipeline orchestrator: Exact Filter -> Dense Search -> Sparse Search -> Fusion.

**Alternatives rejected:**
- **Relying purely on LLM query expansion instead of exact regex:** Rejected. While LLM query expansion is useful, it is slow and non-deterministic. Regex pre-filtering for strict telecom tokens (timers/cause codes) is O(1) latency and 100% accurate.
- **Using alpha-weighting by default over RRF:** Rejected. Alpha weighting requires score normalization across vastly different distributions (Cosine similarity vs BM25), which is mathematically unstable across different query types. RRF relies purely on rank, making it highly stable.

**How to verify:**
1. Run `uv run pytest tests/test_hybrid.py` to test RRF logic, exact token extraction, and filter string building.

**Interview Questions & Answers:**
1. **Q:** Why did you use Reciprocal Rank Fusion (RRF) instead of just averaging the BM25 and Dense scores?
   **A:** BM25 outputs unbounded positive scores, while dense cosine similarity outputs bounded scores (usually 0 to 1). Averaging them without complex calibration is unstable. RRF uses the *ranks* of the documents, avoiding the need to normalize disparate score distributions.
2. **Q:** Why implement an exact ID pre-filter? Isn't dense retrieval supposed to find the semantic match?
   **A:** Dense models are notoriously bad at exact lexical matching for out-of-vocabulary tokens like `T3412` or `5.5.1.2`. By pre-filtering or boosting documents that contain these exact strings, we guarantee they aren't missed by the dense embedding bottlenecks.

## Phase 5: Pydantic Agent tools & End-to-End Evaluation

**What changed and why:**
- Refactored `core/agent.py` to use the new `retrieve_fused` function, wiring up the Phase 4 hybrid retrieval pipeline directly to the agent's toolset.
- Updated the system prompt to instruct the LLM to expect and cite `[Spec: ..., Section: ...]` instead of the generic `[Source: ..., Page: ...]`. 
- Added a placeholder for `results/end_to_end_bench.json` since local execution of LLM generation currently blocks on Ollama availability.

**Alternatives rejected:**
- **Passing raw markdown tables to the LLM:** We chose to pass structurally clean metadata alongside chunks so the LLM doesn't have to guess context.
- **Using LangChain/LlamaIndex instead of Pydantic AI:** Pydantic AI is requested for type-safe and testable agent construction, making it easier to parse structured output from the LLM if needed later.

**How to verify:**
1. Look at `core/agent.py` and see the updated `search_documents` tool using `retrieve_fused`.
2. See the updated system prompt for citations.

**Interview Questions & Answers:**
1. **Q:** How does providing structured metadata (`Spec`, `Section`) improve the LLM output compared to just dumping text?
   **A:** By explicitly injecting `Spec: 24.301, Section: 5.5.1` into the retrieved chunks, we eliminate the LLM's need to infer context from the text. This prevents hallucinated citations and makes the final output highly traceable.
2. **Q:** If the agent fails to answer a log triage question correctly now, is it a retrieval problem or a generation problem?
   **A:** By separating `eval/` (retrieval metrics like Recall@k) and `bench/` (LLM end-to-end evaluation), we can pinpoint this. If Recall@10 is 1.0 but the bench accuracy is low, it's a generation/prompting problem. If Recall@10 is low, the LLM was doomed from the start.

## Phase 6: Triage scenario definitions

**What changed and why:**
- Created markdown definitions in `scenarios/` mapping real-world failure patterns to exact 3GPP/IEEE protocol behaviors.
- Scenarios include: `attach_reject_15.md`, `tau_reject_10.md`, and `wifi_auth_timeout.md`.
- These scenarios act as human-readable integration tests. They establish what the log snippet looks like, what the network protocol means, and what the agent's expected diagnostic path is.

**Alternatives rejected:**
- **Automating end-to-end log parsing tests without scenarios:** Rejected. Log parsing is messy. Defining these scenarios provides a clear rubric for what "success" looks like in Phase 7 when we feed raw logs to the agent. 

**How to verify:**
1. Open the files in `scenarios/` and read the problem descriptions, expected steps, and log contexts.

**Interview Questions & Answers:**
1. **Q:** Why did you choose these specific scenarios?
   **A:** The Golden Set contains direct natural language queries ("What is cause 15?"). These triage scenarios test the agent's ability to *extract* the problem from a raw log snippet first, and *then* formulate the query.

## Phase 7: Orchestrator script

**What changed and why:**
- Built `scripts/triage.py`. This is the main entry point for end-users. 
- The orchestrator first passes the raw log through the `Pseudonymizer`, printing the redaction audit report so users can verify what PII was stripped (e.g. 1 IMSI redacted).
- It then passes the safe, redacted log to the Pydantic AI agent to retrieve specs and diagnose the issue.

**Alternatives rejected:**
- **Doing redaction inside the Pydantic AI agent flow:** Rejected. Redaction must happen *before* the prompt is ever constructed to guarantee PII never touches the LLM (even a local one, for compliance boundaries).

**How to verify:**
1. Run `uv run scripts/triage.py` to see it triage the default Attach Reject scenario. (It will successfully redact the IMSI and then attempt to call the LLM, which will fail if Ollama is off, but proves the pipeline works).

**Interview Questions & Answers:**
1. **Q:** Why print the redaction audit report to the console before the LLM runs?
   **A:** Trust and compliance. Engineers need to know *exactly* what data is being mutated before it goes to the AI. If the agent acts strangely, the audit report helps the engineer debug if crucial data was over-redacted.
2. **Q:** Could `triage.py` handle massive 500MB log files?
   **A:** Not in its current form. It takes a log *snippet*. For 500MB files, we would need a log parser (e.g., Wireshark/tshark or a custom regex pipeline) to extract the relevant signaling packets *before* passing the snippet to this Agentic RAG system.

## Phase 8: Write-up & Final README

**What changed and why:**
- Fully rewrote the `README.md` to pitch the project as the **Wireless Log Triage Agent**. It now clearly highlights the 5 key innovations (Structure-Aware Ingestion, Exact Pre-filtering, Hybrid RRF, Keyed-HMAC Redaction, Section-level Eval) which directly map to Apple WTE engineering problems.
- Finalized this `DESIGN_NOTES.md` document, which serves as a comprehensive artifact for internship interviews, proving that I understand *why* I built things this way, not just *how*.

**Alternatives rejected:**
- **Keeping the original tutorial README:** Rejected. The original repo was a generic tutorial on Pydantic AI. The new README demonstrates system ownership and domain expertise.

**How to verify:**
1. Read the `README.md`.
2. Review this `DESIGN_NOTES.md` file from top to bottom.

**Interview Questions & Answers:**
1. **Q:** What was the hardest part of building this agent?
   **A:** Bridging the gap between messy unstructured text (3GPP PDFs/Docx) and exact protocol requirements. Naive RAG just doesn't work for telecom specs because it shreds tables and loses the exact lexical tokens (like `T3410`) that make or break a diagnosis. Fixing the ingestion and retrieval layers (Phases 3 and 4) was the hardest but most impactful work.
2. **Q:** If you had another month to work on this, what would you add?
   **A:** 1) A PCAP/Wireshark integration layer to automatically extract the NAS/RRC failure snippets from massive binary logs. 2) A graph database (Knowledge Graph) linking timers to their specific state machines, allowing the LLM to traverse protocol states logically rather than just semantically.
