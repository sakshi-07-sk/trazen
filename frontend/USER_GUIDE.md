# CryptoTrace — Investigation Command Center
## User Guide & Forensic Engineering Documentation
**Role 4 — Senior Frontend, AI Product & Data Visualization Specialist**

---

## 1. Executive Summary

**CryptoTrace** is an enterprise-grade forensic blockchain intelligence and investigation platform engineered for cybersecurity incident responders, anti-money-laundering (AML) analysts, law enforcement investigators, and threat intelligence units.

Unlike generic cryptocurrency tracking dashboards or admin portals, CryptoTrace adopts a professional Security Operations Center (SOC) forensic aesthetic with restrained navy/charcoal styling, cryptographic verification ledgers, Cytoscape.js interactive graph topologies, and a deterministic TraceAI copilot grounded strictly in verified evidence without hallucinations.

---

## 2. Architecture & Ownership Boundaries

CryptoTrace is structured according to strict separation of concerns:

- **Role 1 (Ingestion & Ledger Data):** Blockchain RPC consensus node clients (Geth, Bitcoin Core), transaction receipts, block headers, address normalization, and graph adjacency lists.
- **Role 2 (Forensic Scoring & Detection Rules):** Anomaly algorithms, peel-chain heuristics, high-velocity layering detection, mixer deposit tracking, and candidate destination scoring.
- **Role 3 (Security Detection & Tamper-Evident Ledger):** Detection rule catalog, SHA-256 hash-chain audit ledger, Merkle checkpoint proofs, and evidence vault integrity verification.
- **Role 4 (You / This Implementation):** Complete user-facing Next.js 14 application, Cytoscape.js visualization engine, wallet intelligence views, risk indicators, TraceAI copilot, report generation engine, Playwright test suite, and end-to-end integration.

```
frontend/src/
  ├── app/
  │    ├── api/
  │    │    ├── stats/route.ts                 # SOC KPI metrics
  │    │    ├── investigations/route.ts        # Investigation creation & listing
  │    │    ├── investigations/[id]/route.ts   # Case details with full graph
  │    │    ├── copilot/route.ts               # Grounded TraceAI assistant
  │    │    └── audit/verify/route.ts          # Cryptographic SHA-256 verifier
  │    ├── globals.css                         # Sleek SOC dark theme & scrollbars
  │    ├── layout.tsx                          # Root metadata and typography
  │    └── page.tsx                            # Primary unified workspace
  ├── components/
  │    ├── common/                             # Badges, Buttons, Cards, RiskMeter
  │    ├── graph/                              # CytoscapeGraph canvas & filters
  │    └── layout/                             # AppNavbar & navigation tabs
  ├── features/
  │    ├── investigations/                     # CommandCenter, NewInvestigation, Timeline
  │    ├── wallets/                            # WalletDetailPanel & directory
  │    ├── findings/                           # SuspiciousFindingsView & filters
  │    ├── intelligence/                       # ReceiverIntelligenceView & ethics
  │    ├── audit/                              # EvidenceVaultView & hash-chain
  │    ├── copilot/                            # TraceAICopilotPanel assistant
  │    └── reports/                            # InvestigationReportModal & exports
  ├── services/api/                            # Reusable Typed API Client
  ├── lib/                                     # Mock datasets, validation, formatting
  └── types/                                   # Shared Role 1-3 TypeScript contracts
```

---

## 3. Design System & Cybersecurity Aesthetic

CryptoTrace employs a dark cybersecurity aesthetic inspired by enterprise threat intelligence platforms:

- **Palette:**
  - Base Background: Deep charcoal / navy (`#070b14`)
  - Elevated Surfaces: Dark slate glass (`#0d131f` / `#111827`)
  - Borders: Subtle steel hairline borders (`#1e293b`)
  - Restrained Blue & Violet Accents: Primary action (`#3b82f6`), Bridge indicator (`#8b5cf6`)
  - Threat Crimson: Critical anomaly / mixer (`#ef4444`)
  - Warning Amber: High risk / peel-chain (`#f59e0b`)
  - Verification Emerald: Cryptographically sealed ledger (`#10b981`)
- **Typography:** Crisp monospaced numerals, hash formatting, and clean tabular data hierarchies.

---

## 4. Main Application Screens

### A. Investigation Command Center
- **Key Metrics:** Total active cases, analyzed wallets, traced multi-hop transactions, suspicious rule hits, high-priority triages, and SHA-256 ledger status.
- **Mode Indicators:** Clear distinction between `DEMO FORENSIC DATASET` and `LIVE CONSENSUS NODE`.
- **Repository Table:** Recent investigations with instant access to case dossiers and interactive graphs.
- **Threat Alerts Feed:** Real-time stream of detected OFAC sanction matches, UTXO peel chains, and cross-chain bridge relays.

### B. New Investigation Workflow
- **Multi-Chain Support:** Bitcoin (Legacy 1..., Script 3..., Bech32 bc1...) and Ethereum (0x... 40-char addresses and 64-char tx hashes).
- **Format Validation:** Real-time regex and checksum verification preventing invalid queries.
- **Ingestion Mode:** Supports both Demo Forensic Replay and Live Consensus RPC nodes.
- **Provider Error Resilience:** If live RPC keys are unavailable, CryptoTrace presents an explicit error banner and **never fabricates counterfeit data for live requests**.
- **Sample Quick-Loads:** One-click pre-sets for the Lazarus Multi-Hop Mixer Case and Ransomware UTXO Peel Chain.

### C. Interactive Trace Explorer (Cytoscape.js)
- **Node Styles:**
  - *Target Ingress Wallet:* Golden hexagon with high-visibility target border.
  - *Transit / Intermediary Wallets:* Slate rounded ellipses with threat-coded borders.
  - *Mixer Privacy Pools (Tornado Cash / Wasabi):* Red star nodes with threat glows.
  - *Cross-Chain Bridges (Stargate):* Violet diamond nodes.
  - *Smart Contracts & DEX Pools:* Cyan rectangles.
- **Edge Layers:**
  - *Confirmed On-Chain Transfer:* Solid blue directed vector with transfer amount.
  - *UTXO Spending Flow:* Solid amber vector with unspent output link.
  - *Token Transfer (ERC-20 USDT):* Cyan dashed line.
  - *Bridge Correlated Transfer:* Violet dotted line.
  - *Heuristic / Peel Chain Link:* Red dashed line with heuristic rationale.
- **Controls:** Canvas zoom, pan, fit view, breadthfirst layout reset, search filter, hop-depth slider, minimum amount filter, and relationship layer toggles.

### D. Wallet Intelligence View
- **Observability Principle:** Prominently distinguishes *Direct On-Chain Observations* (verified balance, block receipts) from *Inferred Cluster Logic* (entity tags, attribution heuristics).
- **Activity Metrics:** Current balance, lifetime transaction volume, total ingress, and total egress.
- **Flow Breakdown:** Ingress flows vs egress flows with transaction hashes, block numbers, and confidence ratings.
- **Connected Findings:** Active anomaly detections specifically affecting the inspected wallet.

### E. Suspicious Activity Dashboard
- **Detection Rules:** Detailed breakdown of rule IDs (e.g. `RULE-SANCTION-OFAC-V3`, `RULE-PEEL-CHAIN-V2`).
- **Severity & Status:** Filter by severity (Critical, High, Medium, Low) and status (Active, Triaged, Dismissed).
- **Defensive Caveats:** Technical explanation alongside limitations and false-positive caveats (e.g., distinguishing automated peel chains from exchange sweeps).

### F. Receiver Intelligence & Destination Attribution
- **Ranked Candidates:** Candidate end receivers ranked by flow concentration, attribution confidence %, and taint coverage %.
- **Attribution Ethics & Restraint Principle:** Prominent compliance notice stating that public blockchain addresses represent cryptographic accounts and analysis models fund destination probability without claiming to assert real-world personal identity.

### G. Investigation Timeline
- **Chronological Rail:** Integrated timeline tracing transaction events, cross-chain bridge events, forensic findings, analyst milestones, and cryptographic audit checkpoints.
- **Navigation Controls:** Sort by newest or oldest, filter by event type.

### H. Evidence Vault & Cryptographic Verification
- **Artifact Records:** Ingested block numbers, consensus RPC providers, raw payload hashes, and detection rule versions.
- **Tamper-Evident Hash-Chain:** Consecutive SHA-256 Merkle links where each record cryptographically signs the previous record hash.
- **One-Click Audit Verification:** Live verification verifying the chain integrity from genesis to the head hash.

---

## 5. TraceAI Copilot

An interactive investigator assistant slide-over drawer:
- **Grounded Responses:** Strictly bound to structured case findings, nodes, and evidence records.
- **No Hallucinations:** Does not invent non-existent transactions, entities, or wallets.
- **Evidence Citations:** Formats supporting evidence IDs and detection rule references as interactive badges.
- **Offline Fallback:** If an external LLM provider is offline or unconfigured, the built-in deterministic forensic reasoning engine automatically processes queries without blocking investigator workflows.

---

## 6. Investigation Dossier Report Generation

Produces a comprehensive forensic report:
1. Case Identification & Target Scope
2. Transaction Trail & Graph Topology Summary
3. Suspicious Activity Findings Matrix
4. Candidate Destination End Receivers
5. Tamper-Evident Audit & Data Provenance (SHA-256 Proof)
6. Limitations & Restraint Notice
- **Export Capabilities:** Print / Save to PDF (`window.print()`), Markdown export (`.md`), and raw structured JSON export (`.json`).
- **Synthetic Data Label:** Clearly tags synthetic demonstration cases.

---

## 7. Running the Application & Test Suites

### Prerequisites
- Node.js v18+ (tested on Node.js v26)
- npm v10+

### Installation & Build
```bash
# Navigate to the frontend directory
cd C:\Users\varsh\.gemini\antigravity\scratch\cryptotrace\frontend

# Install dependencies (already completed)
npm install

# Production build
npm run build

# Start production server
npm run start
```
The application will be accessible at `http://localhost:3000`.

### Running Tests
CryptoTrace includes a three-tier test suite:
```bash
# 1. Run Cryptographic Validation Unit Tests (9 passed)
npm run test:unit

# 2. Run API Endpoint Integration Tests (17 passed)
npm run test:integration

# 3. Run Playwright E2E Test Suite (10 passed)
npm run test

# 4. Run All Test Suites
npm run test:all
```

---

## 8. Definition of Done Checklist

| Requirement | Implementation | Status |
|:---|:---|:---:|
| 1. Enter wallet or transaction hash | Validated in `NewInvestigationForm` for ETH & BTC | ✅ Verified |
| 2. Start an investigation | Automated ingestion with progress states | ✅ Verified |
| 3. View transaction graph | Cytoscape.js directed graph with customized node/edge styling | ✅ Verified |
| 4. Expand and inspect connected wallets | `WalletDetailPanel` with flows, balance, and risk score | ✅ Verified |
| 5. Examine suspicious findings | `SuspiciousFindingsView` with severity filters & detection rules | ✅ Verified |
| 6. Review destination rankings | `ReceiverIntelligenceView` with attribution % and ethics disclaimer | ✅ Verified |
| 7. Ask TraceAI grounded questions | `TraceAICopilotPanel` with evidence citations & offline fallback | ✅ Verified |
| 8. Generate investigation report | `InvestigationReportModal` with Print/PDF, Markdown, & JSON | ✅ Verified |
| 9. Verify audit history | `EvidenceVaultView` with SHA-256 sequential hash-chain verification | ✅ Verified |
| 10. Playwright & unit test suites | 10 Playwright E2E + 9 Unit + 17 API tests all passing | ✅ Verified |
