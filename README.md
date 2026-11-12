# CryptoTrace — Blockchain Forensics & Threat Intelligence Platform

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.2+-orange.svg)](https://networkx.org/)
[![Cytoscape.js](https://img.shields.io/badge/Cytoscape.js-3.28+-blue.svg)](https://js.cytoscape.org/)
[![Tests](https://img.shields.io/badge/tests-68%20passed-brightgreen.svg)](tests/)

**CryptoTrace** is an enterprise-grade blockchain forensic investigation and threat intelligence platform designed for compliance analysts, law enforcement investigators, and cybersecurity teams. 

The platform integrates multi-chain transaction ingestion, graph network traversal, deterministic forensic heuristics, explainable machine learning, and an interactive investigation command center into an end-to-end investigative pipeline.

---

## 🏛️ System Architecture & Subsystems

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                       CryptoTrace Platform Architecture                        │
└────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
       ┌─────────────────────────────────────────────────────────────────┐
       │       Role 1: Blockchain Data Foundation (cryptotrace/)         │
       │  • Bitcoin UTXO & Ethereum Account Adapters                     │
       │  • Canonical Transaction Normalization Pipeline                 │
       │  • PostgreSQL + SQLAlchemy 2.0 Async + Alembic                  │
       │  • NetworkX Directed Graph & Multi-Hop Traversal (1-3 hops)     │
       │  • Inflow / Outflow Accounting & Cryptographic Provenance       │
       └─────────────────────────────────────────────────────────────────┘
                                        │
                           Investigation Case & Graph
                                        │
                                        ▼
       ┌─────────────────────────────────────────────────────────────────┐
       │       Role 2: Forensic Intelligence Engine (forensics/)         │
       │  • CIOH Wallet Clustering with CoinJoin / PayJoin Safeguards     │
       │  • Peel-Chain & Pass-Through Structuring Detectors              │
       │  • Equal-Denomination Mixing & Fan-In / Fan-Out Analysis        │
       │  • Cross-Case Shared Infrastructure Analysis                    │
       │  • 4-Dimensional Risk & Explainable End-Receiver Ranking        │
       │  • Unsupervised ML (Isolation Forest, DBSCAN) Benchmark        │
       └─────────────────────────────────────────────────────────────────┘
                                        │
                   Forensic Findings, Risk Scores & Candidates
                                        │
                   ┌────────────────────┴────────────────────┐
                   ▼                                         ▼
       ┌────────────────────────┐               ┌────────────────────────┐
       │  Role 3: Threat Intel  │               │ Role 4: Command Center │
       │  & Security Scoring    │               │  Web UI (frontend/)    │
       └────────────────────────┘               └────────────────────────┘
```

---

## 🚀 Key Capabilities

### 1. Multi-Chain Ingestion & Data Foundation (`cryptotrace/`)
* **Bitcoin UTXO Modelling**: Captures distinct inputs, outputs, and script types without fabricating false 1-to-1 input-to-output attributions. Intermediate transaction nodes ensure exact graph topology.
* **Ethereum Account & Token Tracing**: Full support for native ETH transfers, ERC-20 token transfers, and smart contract execution traces.
* **Strict Monetary Precision**: Zero floating-point rounding errors—all monetary values are strictly handled via Python `Decimal` and database `Numeric(38, 18)`.
* **Reliability & Audit Provenance**: Token-bucket rate limiting, exponential backoff with jitter, async TTL caching, and SHA-256 cryptographic provenance hashing for every retrieved transaction.
* **Deterministic Offline Mode**: Built-in deterministic mock adapters allow complete offline testing and demonstration without external API keys.

### 2. Forensic Intelligence Engine (`forensics/`)
* **Clustering & CoinJoin Safeguards**: Common-Input Ownership Heuristic (CIOH) clustering with automatic suppression for collaborative transactions (CoinJoin/PayJoin) and strict exclusion of distinct verified services.
* **Peel-Chain Identification**: Detects automated peeling chains across Bitcoin and Ethereum while discarding benign intermediary hops (exchanges, payment processors).
* **Structuring & Dormancy Analysis**: Identifies rapid fan-in/fan-out structuring, burst splits, and reactivation of long-dormant wallets (30+ days).
* **Cross-Case Infrastructure Correlation**: Discovers overlapping money-laundering sinks and traversal paths across separate investigations while filtering benign public services.
* **4-Dimensional Risk Assessment**: Rather than relying on a single opaque score, each wallet is evaluated across 4 independent dimensions:
  1. `risk_priority`: Weighted triage urgency.
  2. `attribution_confidence`: Evidence solidity based on confirmed vs. inferred edges.
  3. `known_risk_exposure`: Hop-decayed proximity to illicit services (mixer exposure capped at 0.45 without corroborated links).
  4. `investigation_coverage`: Graph completeness factoring observable transactions.
* **Ranked Candidate Sinks**: Computes candidate destination paths without asserting false real-world human identity claims.

### 3. Investigation Command Center Web UI (`frontend/`)
* **SOC KPI & Case Repository**: Interactive overview of active forensic cases, total exposure volumes, and high-severity threat alerts.
* **Cytoscape.js Forensic Trace Graph**: Visual multi-hop graph explorer supporting circular, hierarchical, and breadth-first layouts, color-coded edges (confirmed transfers, UTXO inputs/outputs, ERC-20 tokens, peel chains), and inspector drawers.
* **Evidence Vault & Audit Receipts**: Cryptographic consensus receipts and SHA-256 hash-chain verification for court-ready admissibility.
* **TraceAI Forensic Copilot**: Evidence-grounded conversational analyst with offline deterministic fallback responses.
* **Dossier Exporter**: Generation of investigation dossiers in PDF, Markdown, and structured JSON formats.

---

## 📁 Repository Layout

```text
Codespark/
├── alembic/                      # Database migrations
│   └── versions/
│       └── 0001_initial_crypto_trace_schema.py
├── alembic.ini                   # Alembic configuration
├── cryptotrace/                  # [Role 1] Blockchain Data Subsystem
│   ├── api/                      # REST endpoints & dependencies
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/        # /health, /investigations
│   ├── connectors/               # Bitcoin & Ethereum connectors + fixtures
│   ├── core/                     # Logging, caching, rate limiting, retry
│   ├── db/                       # SQLAlchemy models & repositories
│   ├── graph/                    # NetworkX graph engine & BFS traversal
│   ├── normalization/            # UTXO & account normalizers
│   ├── schemas/                  # Shared Pydantic contracts
│   ├── services/                 # Ingestion & investigation orchestrators
│   ├── config.py                 # Pydantic Settings
│   └── main.py                   # Role 1 FastAPI application
├── forensics/                    # [Role 2] Forensic Intelligence Subsystem
│   ├── api/                      # Forensics endpoints (/findings, /risk, /analyze)
│   ├── datasets/                 # Deterministic benchmark fixtures & synthetic ML data
│   ├── detectors/                # Clustering, peel-chain, mixer, structuring, cross-case
│   ├── features/                 # 17 behavioral wallet feature extractors
│   ├── graph/                    # Single-pass graph indexing & caching
│   ├── ml/                       # Isolation Forest, DBSCAN, Random Forest evaluation
│   ├── schemas/                  # Findings, risk, and ranking contracts
│   ├── scoring/                  # 4D risk and candidate receiver ranking
│   └── engine.py                 # Unified forensics orchestrator
├── frontend/                     # [Role 4] Next.js 14 Forensic Command Center
│   ├── app/                      # App Router pages (/investigations, /graph, /reports)
│   ├── components/               # Cytoscape graph, panels, AI copilot, timeline
│   ├── lib/                      # API client, offline mock store, report generation
│   ├── public/                   # Static assets & icons
│   └── USER_GUIDE.md             # Complete frontend analyst manual
├── config/
│   └── forensics_config.yaml     # Tunable forensics thresholds and heuristics
├── docker/
│   └── Dockerfile                # Multi-stage production container build
├── scripts/
│   └── run_evaluation.py         # Benchmark and ML evaluation script
├── tests/                        # 68 unified automated tests
├── ARCHITECTURE.md               # Detailed technical architecture document
├── FORENSICS.md                  # Comprehensive Role 2 forensic specification
├── docker-compose.yml            # PostgreSQL & service orchestration
├── pyproject.toml                # Build system & dependencies
└── README.md                     # Platform documentation
```

---

## ⚡ Quickstart

### 1. Requirements
* Python 3.11+
* Node.js 18+ & npm (for `frontend/`)
* Git

### 2. Backend Setup

```bash
# Clone the repository
git clone https://github.com/sakshi-07-sk/trazen.git
cd trazen

# Create and activate virtual environment
python -m venv .venv
# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -e ".[dev]"

# Configure environment variables
cp .env.example .env

# Apply database migrations
alembic upgrade head
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run build
```

---

## 🖥️ Running the Services

### Role 1: Blockchain Data & Ingestion Service
```bash
uvicorn cryptotrace.main:app --host 0.0.0.0 --port 8000 --reload
```
* **Swagger UI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### Role 2: Forensic Intelligence Engine
```bash
uvicorn forensics.api.app:app --host 0.0.0.0 --port 8001 --reload
```
* **Forensics API Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)

### Role 4: Investigation Command Center (Frontend)
```bash
cd frontend
npm run dev
```
* **Interactive UI**: [http://localhost:3000](http://localhost:3000)

---

## 🐳 Docker Deployment

To launch the complete backend alongside PostgreSQL 16:

```bash
docker compose up --build
```

---

## 🧪 Testing & Benchmark Evaluation

### Python Backend Test Suite (68 Tests)
Execute the complete offline Pytest test suite:
```bash
python -m pytest -v
```

### Forensic Heuristic Benchmark & ML Evaluation
Run reproducible evaluation across 11 controlled scenarios and synthetic anomaly models:
```bash
python -m scripts.run_evaluation
```

### Frontend Verification
```bash
cd frontend
npm run lint
npm run test:all
```

---

## 🔗 Peer Developer Integration Contracts

Shared data models are accessible across submodules:

```python
# Role 1: Graph topology & canonical transactions
from cryptotrace.schemas.contracts import (
    TransactionGraph,
    GraphNode,
    GraphEdge,
    CanonicalTransaction,
    BlockchainType,
    NodeType,
    EdgeType,
)

# Role 2: Forensic findings, 4D risk & receiver rankings
from forensics.schemas import (
    ForensicFinding,
    RiskAssessmentResponse,
    ReceiverCandidate,
    InvestigationFindingsResponse,
)
```

---

## 📄 Documentation Links

- **Backend Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Forensic Engine Specification & Benchmarks**: [FORENSICS.md](FORENSICS.md)
- **Frontend Analyst Manual**: [frontend/USER_GUIDE.md](frontend/USER_GUIDE.md)

---

## 📄 License

CryptoTrace is distributed under the MIT License.
