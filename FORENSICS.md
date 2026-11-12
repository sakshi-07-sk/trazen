# CryptoTrace — Forensic Intelligence Engine (`FORENSICS.md`)

**Role 2 Subsystem Specification, Feature Definitions, Methodology & Evaluation Report**

---

## 1. Architecture & Integration Boundaries

The Forensic Intelligence Engine transforms normalized blockchain transactions and graph structures (supplied by Role 1) into deterministic, evidence-driven, explainable forensic findings, candidate wallet clusters, 4-dimensional risk assessments, and ranked candidate destination paths for Role 3 (security correlation) and Role 4 (visualization).

### Ownership Boundaries
- **Role 1 (Input Provider):** Supplies `InvestigationCase` objects containing normalized UTXO/account transactions, `GraphNode`, `GraphEdge` (with `confirmed` vs `inferred` flags), and `EntityLabel` provenance metadata.
- **Role 2 (This Subsystem):** Single-pass graph indexing & caching, wallet behavioural feature engineering, clustering heuristics with CoinJoin safeguards, peel-chain detection, fan-in/fan-out & mixer analysis, chain-specific structuring & dormancy detection, cross-case infrastructure analysis, explainable ML prioritization, 4-dimensional risk scoring, probable end-receiver ranking, and FastAPI forensic endpoints.
- **Role 3 & Role 4 (Consumers):** Consume standardized `ForensicFinding`, `RiskAssessmentResponse`, and `ReceiverCandidate` contracts via Python services or REST endpoints.

### Confirmed vs. Inferred Relationships
- Every `NormalizedTransaction` and `GraphEdge` preserves `relationship_status: Literal["confirmed", "inferred"]`.
- Direct account-based transfers (`from_address -> to_address`) and single-input UTXO flows retain `confirmed` status when observed directly on-chain.
- Multi-input UTXO leg allocations and heuristic wallet cluster links (`common_input_ownership`, `repeated_bidirectional_counterparty`, `synchronized_transaction_timing`) are strictly tagged `inferred` with bounded confidence (`<= 0.72` for CIOH, `<= 0.85` combined) and explicit counter-evidence.
- Two connected addresses are **never** assumed to belong to the same human owner.

---

## 2. Behavioural Feature Engineering

Implemented as pure, cached functions in [`forensics/features/extractor.py`](file:///c:/Users/SAKSHI%20S%20K/OneDrive/Desktop/trazen/forensics/features/extractor.py) backed by [`InvestigationGraphIndex`](file:///c:/Users/SAKSHI%20S%20K/OneDrive/Desktop/trazen/forensics/graph/index.py).

| Feature | Type | Description |
|---|---|---|
| `inbound_tx_count` / `outbound_tx_count` / `total_tx_count` | `int` | Deduplicated inbound, outbound, and total transaction counts |
| `unique_senders` / `unique_receivers` / `unique_counterparties` | `int` | Distinct upstream senders, downstream receivers, and total counterparties |
| `total_inflow` / `total_outflow` / `net_flow` | `float` | Cumulative received value, sent value, and residual net flow |
| `residual_balance_ratio` | `float` | `max(0, net_flow / total_inflow)` indicating retention vs pass-through |
| `median_tx_value` / `mean_tx_value` / `tx_value_cv` | `float` | Median, mean, and coefficient of variation (`std / mean`) of transfer values |
| `tx_velocity_per_day` | `float` | Transaction frequency normalized over active time span |
| `dormancy_period_seconds` | `float` | Maximum inter-transaction gap observed for the wallet |
| `fan_in_ratio` | `float` | `unique_senders / max(1, inbound_tx_count)` |
| `fan_out_ratio` | `float` | `unique_receivers / max(1, outbound_tx_count)` |
| `known_service_exposure` | `float` | Fraction of unique counterparties carrying any `EntityLabel` |
| `known_risk_service_exposure` | `float` | Fraction of unique counterparties with `high` or `critical` risk labels |
| `bridge_interaction_count` | `int` | Transfers flagged as bridge calls or involving `bridge`-labelled addresses |
| `tx_timing_variation_seconds` | `float` | Population standard deviation of inter-transaction time deltas |
| `utxo_avg_inputs` / `utxo_avg_outputs` | `float` | **Bitcoin UTXO-specific:** average input/output counts per UTXO tx (`0.0` on account chains) |
| `address_reuse_count` | `int` | **Bitcoin UTXO-specific:** count of self-change/multi-spend address reuse events |
| `contract_interaction_ratio` / `token_transfer_ratio` | `float` | **Ethereum account-specific:** proportion of EVM contract calls and token transfers |

### Bitcoin UTXO vs. Ethereum Account-Based Handling
- **Bitcoin UTXO:** Transactions store explicit `inputs` and `outputs` (`UTXOEntry`). Self-change (`input_addr == output_addr`) is excluded from external flow legs while tracked for `address_reuse_count` and peel-chain continuation. Multi-input UTXO flows allocate input shares proportionally and mark cross-address edges as `inferred`.
- **Ethereum Account-Based:** Uses explicit `from_address -> to_address`, `nonce`, `is_contract_call`, `is_token_transfer`, and `is_bridge_interaction` attributes without artificial UTXO multi-input heuristics.

---

## 3. Forensic Detectors & False-Positive Safeguards

All thresholds and weights are externalized in [`config/forensics_config.yaml`](file:///c:/Users/SAKSHI%20S%20K/OneDrive/Desktop/trazen/config/forensics_config.yaml).

### A. Address & Wallet Clustering (`CLUSTER-HEURISTIC-01`, `CLUSTER-ADDR-REUSE-01`, `CLUSTER-COINJOIN-GUARD-01`)
- **Heuristics:** Common-Input Ownership Heuristic (CIOH), UTXO address reuse, bidirectional repeated counterparties, and synchronized outbound timing windows.
- **Safeguards:**
  - **CoinJoin / PayJoin Guard (`is_suspected_collaborative_tx`):** Detects `is_collaborative_hint` / metadata flags or UTXO transactions with `>= 3` distinct input addresses and `>= 3` equal-value outputs (within `0.5%` tolerance). CIOH is **suppressed** on collaborative transactions and logged via `CLUSTER-COINJOIN-GUARD-01`.
  - Distinct verified service labels (`exchange`, `merchant`, `payroll`, `defi_router`, `bridge`, `mixer`) are never merged.
  - Every `ClusterEdgeReason` preserves `heuristic`, `confidence`, `relationship_status="inferred"`, `evidence_refs`, and `counter_evidence`.

### B. Peel-Chain Detection (`PEEL-CHAIN-01`)
- Traces multi-hop forwarding sequences (`>= 3` hops, continuation ratio `0.65–0.995`, inter-hop delay `<= 24h`, chain-specific minimum value).
- Produces ordered `detected_path`, `evidence_refs`, `continuation_ratios`, `residual_balances`, `inter_hop_delays_seconds`, `pattern_strength`, and false-positive limitations.
- **Safeguard:** Intermediate addresses labelled as `exchange`, `cex`, `defi_router`, `bridge`, `payroll`, `merchant`, or `payment_processor` are excluded.

### C. Mixer & Fan-In / Fan-Out Detection (`FAN-IN-01`, `FAN-OUT-01`, `MIXER-PATTERN-01`, `MIXER-EXPOSURE-01`)
- **Strict Non-Mixer Safeguard:** High inbound and outbound transaction counts **never** classify a wallet as a mixer by themselves.
- `MIXER-PATTERN-01` requires either a verified `mixer` label OR structural mixing signatures (e.g., `>= 55%` equal-denomination transfers within `2%` tolerance combined with rapid turnaround `<= 4h` or `>= 8` equal-denomination legs) and excludes benign commercial hubs (`exchange`, `merchant`, `payroll`, `defi_router`).
- Collaborative multi-party UTXO transactions (CoinJoin) are guarded against triggering false `FAN-IN-01` / `FAN-OUT-01` alerts.

### D. Structuring & Dormancy Detection (`STRUCTURING-SPLIT-01`, `STRUCTURING-PASSTHROUGH-01`, `DORMANT-REACTIVATION-01`)
- Chain-specific thresholds in `config/forensics_config.yaml` (e.g., `0.50 BTC` reference threshold for `bitcoin` vs `5.0 ETH` for `ethereum`).
- Identifies burst splitting (`>= 4` similar/threshold-avoidance transfers within window) and rapid aggregation-forwarding (`>= 80%` pass-through within `1800s–3600s`).
- Detects reactivation bursts following `>= 30 days` of dormancy while excluding `exchange`, `payroll`, `merchant`, and `mixer` pools from structuring split alerts.

### E. Cross-Case Analysis (`CROSS-CASE-DEST-01`, `CROSS-CASE-PATH-01`, `CROSS-CASE-NODE-01`)
- Compares multiple `InvestigationCase` graphs for shared unlabelled sinks, overlapping multi-hop paths, and shared intermediary wallets.
- **Safeguard:** Public hubs (`exchange`, `cex`, `payment_processor`, `defi_router`, `bridge`) are filtered into `ignored_public_hubs` so normal shared exchange usage does not generate false shared-infrastructure findings.

---

## 4. Risk, Attribution & End-Receiver Ranking

### 4-Dimensional Risk & Attribution Engine ([`forensics/scoring/risk.py`](file:///c:/Users/SAKSHI%20S%20K/OneDrive/Desktop/trazen/forensics/scoring/risk.py))
Outputs four independent `[0.0, 1.0]` dimensions rather than a single opaque score:
1. **`risk_priority`:** Weighted triage priority from rule severity, finding density, known-risk exposure, and dampened anomaly signal.
2. **`attribution_confidence`:** Support strength derived from confirmed vs inferred edge ratio, top path consistency, finding confidence, and graph coverage.
3. **`known_risk_exposure`:** Hop-decayed (`0.55^hop`) proximity to `high`/`critical` risk indicators. Mixer exposure without a corroborated illicit link is capped at `0.45`.
4. **`investigation_coverage`:** Graph completeness factoring `is_graph_complete`, `observed_in_full`, `missing_neighbors_estimated`, and availability of detailed transactions.

Every assessment includes `contributing_factors`, `supporting_finding_ids`, `counter_evidence`, `confidence_limitations`, and `scoring_rule_version`.

### Probable End-Receiver Ranking ([`forensics/scoring/ranking.py`](file:///c:/Users/SAKSHI%20S%20K/OneDrive/Desktop/trazen/forensics/scoring/ranking.py))
Ranks `candidate_destination` addresses (never asserting human owner identity) using configurable weights across trace-path position, value proportion, path consistency, supporting findings, label provenance, and investigation coverage, with per-candidate `risk_priority`, `attribution_confidence`, `counter_evidence`, and `limitations`.

---

## 5. ML Implementation & Evaluation Report

Implemented in [`forensics/ml/`](file:///c:/Users/SAKSHI%20S%20K/OneDrive/Desktop/trazen/forensics/ml):
- **Isolation Forest ([`anomaly.py`](file:///c:/Users/SAKSHI%20S%20K/OneDrive/Desktop/trazen/forensics/ml/anomaly.py)):** Cohort anomaly prioritization with per-feature z-score explanations. Explicitly labelled as statistical deviation priority, **not** criminality probability.
- **DBSCAN ([`clustering.py`](file:///c:/Users/SAKSHI%20S%20K/OneDrive/Desktop/trazen/forensics/ml/clustering.py)):** Unsupervised behavioural cohort discovery in standardized feature space.
- **Random Forest ([`supervised.py`](file:///c:/Users/SAKSHI%20S%20K/OneDrive/Desktop/trazen/forensics/ml/supervised.py)):** Trained and evaluated strictly on a clearly marked synthetic archetype dataset (`n = 240`, `SYNTHETIC_DEMO_DATA_ONLY`).

### Deterministic Heuristic Benchmark Results (`python -m scripts.run_evaluation`)
Across 11 controlled scenarios (normal retail, ETH peel chain, BTC UTXO peel chain, fan-in, fan-out, mixer pool, structuring + pass-through, dormant reactivation, exchange hot wallet negative guard, payroll negative guard, CoinJoin CIOH guard):
- **True Positives:** `9` | **False Positives:** `0` | **False Negatives:** `0` | **True Negatives:** `26`
- **Precision:** `1.0000` | **Recall:** `1.0000` | **F1-score:** `1.0000`

### Synthetic ML Evaluation Results (`n = 240`, 70/30 stratified split, `support = 72`)

| Model | Precision | Recall | F1-score | Confusion Matrix `[[TN, FP], [FN, TP]]` |
|---|---:|---:|---:|---|
| Majority-Class Dummy Baseline | 0.0000 | 0.0000 | 0.0000 | `[[43, 0], [29, 0]]` |
| Simple Volume/Unlabelled Heuristic Baseline | 0.9474 | 0.6207 | 0.7500 | `[[42, 1], [11, 18]]` |
| Isolation Forest (Unsupervised Anomaly Prioritization) | 0.2000 | 0.2069 | 0.2034 | `[[19, 24], [23, 6]]` |
| Random Forest (Synthetic Behavioural Archetypes Only) | 1.0000 | 1.0000 | 1.0000 | `[[43, 0], [0, 29]]` |

- **5-fold Stratified CV F1 (Synthetic Random Forest):** `1.0000 (+/- 0.0000)`.
- **False-Positive Analysis:**
  - *Simple Volume Heuristic Baseline:* `1` false positive on `retail_user` due to overlapping outbound velocity/unlabelled counterparty counts.
  - *Isolation Forest:* `24` false positives (`18` `retail_user` variance tails, `6` `exchange_hot_wallet` high-volume outliers). This empirically demonstrates why unsupervised anomaly scores identify statistical outliers (such as high-throughput exchange wallets) for analyst triage rather than serving as criminality predictions.
  - *DBSCAN:* Partitioned the 240 synthetic wallets into `10` dense behavioural clusters and `35` outlier points.

---

## 6. Shared Output & API Contract

Implemented in [`forensics/api/router.py`](file:///c:/Users/SAKSHI%20S%20K/OneDrive/Desktop/trazen/forensics/api/router.py):
- `GET /api/v1/investigations/{id}/findings` → `InvestigationFindingsResponse` containing `ForensicFinding` items matching the Section 8 JSON contract (`finding_id`, `rule_id`, `rule_version`, `title`, `category`, `severity`, `confidence`, `explanation`, `evidence_refs`, `limitations`).
- `GET /api/v1/investigations/{id}/risk` → `RiskAssessmentResponse` containing the 4 separate risk/attribution dimensions, `contributing_factors`, `supporting_finding_ids`, `counter_evidence`, `confidence_limitations`, `scoring_rule_version`, `probable_end_receivers`, and `wallet_risks`.
- `POST /api/v1/investigations/{id}/analyze` → Ingests a Role 1 `InvestigationCase` payload and caches the computed `ForensicAnalysisBundle`.
- `POST /api/v1/forensics/cross-case` → Cross-case shared infrastructure analysis.
- `GET /api/v1/forensics/ml-evaluation` → Reproducible ML evaluation report.

### Running Tests & Evaluation
```bash
python -m pytest -v
python -m scripts.run_evaluation
uvicorn forensics.api.app:app --reload
```
