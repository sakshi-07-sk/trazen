# INVESTIGATION_WORKFLOW.md — Trazen (CryptoTrace)
## The 10-Stage Forensic Investigation Lifecycle
**Team Blizzard** | **Project: Trazen (CryptoTrace)**

---

## 1. Overview

Trazen's primary user journey is built around an intuitive, mathematically grounded, and court-admissible 10-stage investigation workflow. Every stage produces verifiable outputs with cryptographic integrity checks.

---

## 2. Stage-by-Stage Forensic Lifecycle

### Stage 1: Platform Discovery & Contextual Orientation
- **User Action:** The investigator lands on the Trazen Command Center or Home portal.
- **System Output:** The investigator is presented with clear problem framing—explaining why multi-chain forensics requires UTXO/Account separation, how peel-chains and mixing obfuscate funds, and why black-box scoring fails in court.
- **Interface Component:** `HeroSection.tsx`, `ProblemSection.tsx`, and `Navbar.tsx`.

### Stage 2: Problem Scope Comprehension
- **User Action:** The investigator reviews active threat indicators, SOC KPIs (total monitored volume, active alerts, compromised wallets), and the 4-dimensional risk paradigm.
- **System Output:** High-level overview of active forensic cases, triage priorities, and data provenance status (`LIVE CONSENSUS NODE` vs `DEMO REPLAY`).
- **Interface Component:** `CommandCenter.tsx`, `StatisticsStrip.tsx`, and `TechnologySection.tsx`.

### Stage 3: Investigation Initialization
- **User Action:** The investigator initiates a new forensic case by selecting network parameters (Ethereum EVM vs Bitcoin UTXO), target identifier type (Wallet Address vs Transaction Hash), and maximum hop expansion depth (1 to 5 hops).
- **System Output:** Configuration modal with instant sample quick-load options for benchmark attack scenarios (Lazarus Group Ingress Target & Darknet Ransomware Campaign).
- **Interface Component:** `NewInvestigationForm.tsx` (Route: `/investigations` or `/dashboard`).

### Stage 4: Data Selection & Ingestion
- **User Action:** The investigator selects their preferred ingestion mode:
  1. **Synthetic Demo Replay:** Deterministic consensus archive replay for offline evaluation.
  2. **Direct Consensus Query:** Querying live Ethereum or Bitcoin node providers.
  3. **Direct Transaction Import:** Uploading or pasting raw JSON / CSV transaction records with custom fields (`txHash`, `from`, `to`, `amount`, `timestamp`).
- **System Output:** Ingestion progress indicator displaying real-time pipeline status: Checksum Validation -> Consensus Ingestion -> Graph Expansion -> Anomaly Detection -> Evidence Sealing.
- **Interface Component:** `NewInvestigationForm.tsx` & `POST /api/investigations`.

### Stage 5: Cryptographic Validation & Decimal Normalization
- **Processing Logic:**
  - *Validation:* Real-time regex and checksum verification (EIP-55 mixed-case for Ethereum, Base58Check for Bitcoin Legacy/Script, Bech32 for Bitcoin SegWit/Taproot).
  - *Normalization:* Heterogeneous payloads are converted into standard `NormalizedTransaction` records.
  - *Monetary Precision:* Strict Python `Decimal` and TypeScript `BigInt` accounting guarantees exact Satoshi (8 decimals) and Wei (18 decimals) precision without floating-point drift.
- **Evidentiary Output:** Ingested transactions are assigned a SHA-256 payload hash and ingested into the evidence ledger.
- **Interface Component:** `frontend/src/lib/validation.ts` and `cryptotrace/normalization/`.

### Stage 6: Multi-Hop Graph Construction & Entity Clustering
- **Processing Logic:**
  - NetworkX builds a directed adjacency graph extending from the seed target up to the configured hop depth.
  - Intermediate transaction nodes are explicitly modeled for Bitcoin multi-input/output transactions, eliminating false 1-to-1 attribution.
  - Wallet clustering algorithms apply the Common-Input Ownership Heuristic (CIOH) while strictly enforcing the **CoinJoin / PayJoin Guard** (`CLUSTER-COINJOIN-GUARD-01`), suppressing false mergers on collaborative transactions.
- **System Output:** Fully populated graph topology with categorized nodes (Target, Intermediary, Mixer, Bridge, Exchange) and edges (Confirmed Transfer, UTXO Spending, Token Transfer, Heuristic Link).
- **Interface Component:** `cryptotrace/graph/` and `frontend/src/lib/mapper.ts`.

### Stage 7: Suspicious Pattern & Anomaly Detection
- **Processing Logic:** Deterministic detection rules execute against the normalized graph:
  - `PEEL-CHAIN-01`: Identifies linear multi-hop transfers forwarding 65%–99.5% of value with rapid turnaround.
  - `MIXER-PATTERN-01`: Detects equal-denomination splitting combined with high fan-in/fan-out while filtering out commercial exchange hubs.
  - `STRUCTURING-SPLIT-01`: Flags burst sub-threshold transactions within brief temporal windows.
  - `DORMANT-REACTIVATION-01`: Detects sudden high-velocity fund movements from wallets idle for >=30 days.
- **System Output:** Detailed findings matrix with unique Rule IDs, confidence ratings, monetary exposure, and explicit defensive caveats.
- **Interface Component:** `SuspiciousFindingsView.tsx` (Route: `/findings`).

### Stage 8: 4-Dimensional Explainable Risk Scoring
- **Processing Logic:** Evaluates four independent, bounded orthogonal dimensions:
  1. **Risk Priority `[0.0 - 1.0]`:** Weighted triage urgency based on rule severity and finding density.
  2. **Attribution Confidence `[0.0 - 1.0]`:** Ratio of confirmed on-chain vectors to inferred heuristic edges.
  3. **Known Risk Exposure `[0.0 - 1.0]`:** Hop-decayed proximity (`0.55^hop`) to sanctioned entities or mixers.
  4. **Investigation Coverage `[0.0 - 1.0]`:** Completeness metric reflecting graph neighborhood depth.
- **System Output:** Comprehensive risk assessment dashboard with ranked candidate destination sinks and contributing factor explanations.
- **Interface Component:** `RiskMeter.tsx` and `ReceiverIntelligenceView.tsx` (Route: `/risk`).

### Stage 9: Interactive Graph Relationship Exploration
- **User Action:** The investigator manipulates the Cytoscape.js canvas to analyze transaction flows:
  - Pan, zoom, and reset breadthfirst graph layout.
  - Dynamic hop slider filtering (view 1 to 5 hops).
  - Minimum transfer value slider to filter noise.
  - Clicking any node opens a deep-dive drawer showing transaction history, counterparty distribution, and label provenance.
- **Interface Component:** `CytoscapeGraph.tsx` and `WalletDetailPanel.tsx` (Route: `/graph`).

### Stage 10: Court-Ready Report Generation & Evidence Sealing
- **User Action:** The investigator triggers "Export Dossier" from the case toolbar.
- **Processing Logic:**
  - Compiles full investigation metadata, target identifier, and network parameters.
  - Appends complete suspicious findings matrix with detection rule specifications and evidence IDs.
  - Ranks candidate destination wallets with attribution rationale.
  - Validates the unbroken SHA-256 hash chain of custody up to the head record hash.
- **System Output:** Generates downloadable Markdown dossier (`<case-id>-FORENSIC-REPORT.md`) and opens print-to-PDF dialog.
- **Interface Component:** `InvestigationReportModal.tsx` and `EvidenceVaultView.tsx` (Route: `/reports` and `/evidence`).
