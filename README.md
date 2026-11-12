# CryptoTrace — Blockchain Forensics & Threat Intelligence Backend

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.2+-orange.svg)](https://networkx.org/)
[![Tests](https://img.shields.io/badge/tests-35%20passed-brightgreen.svg)](tests/)

CryptoTrace provides an enterprise-grade blockchain forensic data foundation for threat intelligence, fund tracing, and graph visualization. Built with Python 3.12+, FastAPI, SQLAlchemy 2.0 (asyncio), PostgreSQL, Alembic, and NetworkX.

---

## Key Features

- **Multi-Chain Ingestion**: Independent adapters for **Bitcoin** (UTXO architecture) and **Ethereum** (Account-based, ERC-20, smart contracts).
- **No False Attribution**: Bitcoin multi-input/multi-output transactions model explicit intermediate transaction nodes, distinguishing confirmed on-chain edges from co-spend heuristics.
- **Strict Decimal Precision**: Monetary values are computed strictly using `Decimal` representation—never floating-point arithmetic.
- **NetworkX Graph Engine**: Directed forensic graph construction with configurable multi-hop traversal (1 to 3 hops), time/amount filtering, and inflow/outflow accounting.
- **High Reliability & Resilience**: Upstream rate-limiting (token bucket), bounded exponential backoff with jitter, async TTL caching, and duplicate transaction detection.
- **Auditable Provenance**: SHA-256 cryptographic payload hashing for every retrieved blockchain record.
- **Deterministic Offline Fixtures**: Full offline demo and test fixture mode when external API keys are unavailable.

---

## Directory Structure

```text
Codespark/
├── alembic/                      # Alembic database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_crypto_trace_schema.py
├── alembic.ini                   # Alembic configuration
├── cryptotrace/                  # Core application package
│   ├── api/                      # FastAPI routes & dependencies
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── health.py
│   │           └── investigations.py
│   ├── connectors/               # Blockchain adapters & clients
│   │   ├── base.py
│   │   ├── bitcoin/              # Blockstream / Mempool adapter & client
│   │   ├── ethereum/             # Etherscan / RPC adapter & client
│   │   └── fixtures/             # Deterministic mock provider & samples
│   ├── core/                     # Logging, cache, retry, exceptions
│   ├── db/                       # SQLAlchemy models & repositories
│   ├── graph/                    # NetworkX graph engine & traversal
│   ├── normalization/            # Normalizers for BTC and ETH
│   ├── schemas/                  # Shared Pydantic contracts (Roles 2, 3, 4)
│   ├── services/                 # Ingestion & investigation orchestration
│   ├── config.py                 # Pydantic Settings
│   └── main.py                   # FastAPI entrypoint
├── docker/                       # Dockerfile & container setup
│   └── Dockerfile
├── tests/                        # Comprehensive Pytest test suite (34 tests)
├── .env.example                  # Environment configuration template
├── ARCHITECTURE.md               # Detailed technical architecture document
├── docker-compose.yml            # PostgreSQL & backend orchestration
└── pyproject.toml                # Build system & dependencies
```

---

## Quickstart

### 1. Prerequisites
- Python 3.11+
- (Optional) Docker & Docker Compose for containerized PostgreSQL

### 2. Local Installation

```bash
# Clone and enter directory
cd Codespark

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Environment Configuration

Copy the example configuration:
```bash
cp .env.example .env
```

Key environment variables:
- `DEMO_FIXTURE_MODE=true` — Enables deterministic offline fixtures (works with zero external API keys).
- `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cryptotrace` (or `sqlite+aiosqlite:///./cryptotrace.db` for local SQLite).
- `ETHERSCAN_API_KEY=` — Optional Etherscan API key for live Ethereum lookups.
- `BLOCKSTREAM_API_URL=` — Optional custom Bitcoin API endpoint.

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Start the API Server

```bash
uvicorn cryptotrace.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## Running with Docker Compose

To run CryptoTrace alongside a dedicated PostgreSQL 16 database:

```bash
docker compose up --build
```

---

## Running Tests

Execute the complete offline Pytest test suite:

```bash
python -m pytest -v
```

All 35 tests run offline using deterministic fixtures and an in-memory SQLite database.

---

## Peer Developer Integration Rules

The contracts defined in `cryptotrace.schemas.contracts` are stable and frozen for cross-subsystem consumption:

### Role 2 (ML / Forensic Detection Subsystem)
Import graph representations and canonical transactions directly:
```python
from cryptotrace.schemas.contracts import (
    TransactionGraph,
    GraphNode,
    GraphEdge,
    CanonicalTransaction,
    NodeType,
    EdgeType,
)
```

### Role 3 (Threat Intelligence & Risk Scoring Subsystem)
Import canonical transaction records and cryptographic provenance:
```python
from cryptotrace.schemas.contracts import (
    CanonicalTransaction,
    DataSourceProvenance,
    TokenTransfer,
    UTXOOutput,
)
```

### Role 4 (Web Frontend Client Subsystem)
Located in `frontend/` — Built with Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Cytoscape.js, and Playwright:
- **Investigation Command Center:** SOC KPI metrics, multi-case repository, threat alert feed.
- **Interactive Trace Graph:** Cytoscape.js multi-hop graph explorer with custom styling for confirmed transfers, UTXO spending, tokens, cross-chain bridges, and peel chains.
- **Wallet Intelligence View:** Differentiates direct on-chain observations from heuristic cluster inferences.
- **Suspicious Findings Matrix:** Rule anomaly breakdown with technical limitations caveats and severity filtering.
- **Receiver Intelligence:** Ranked destination attribution candidates with ethical restraint notice.
- **Evidence Vault:** Cryptographic consensus RPC receipts and sequential SHA-256 hash-chain verification.
- **TraceAI Copilot:** Evidence-grounded forensic assistant with offline fallback engine.
- **Investigation Dossier:** Printable/PDF, Markdown, and JSON forensic reports.

Quick Start:
```bash
cd frontend
npm install
npm run build
npm run start
```
Run Test Suites:
```bash
cd frontend
npm run test:all
```
For full engineering guide, see [`frontend/USER_GUIDE.md`](frontend/USER_GUIDE.md).
