# DEMO_GUIDE.md — Trazen (CryptoTrace)
## Evaluator Step-by-Step Demonstration Guide
**Competition:** Hack2Skill PromptWars x AI Vibeathon 2026 | **Team Blizzard**

---

## 1. Quick Evaluation Checklist

This guide provides an evaluator with an immediate, foolproof, and fully reproducible walkthrough of Trazen's capabilities. 

All three demonstration pathways work seamlessly both **online** (deployed on Vercel) and **offline** (zero external API keys required).

| Demo Pathway | Ingestion Mode | Input Type | Time to Evaluate | Key Capabilities Demonstrated |
|---|---|---|---|---|
| **Scenario 1: Lazarus Group Ingress Trace** | Synthetic Demo Replay | Ethereum Address | ~2 minutes | Multi-hop mixer detection, cross-chain bridge tracking, 4D risk scoring, Cytoscape graph. |
| **Scenario 2: Ransomware UTXO Campaign** | Synthetic Demo Replay | Bitcoin Bech32 Address | ~2 minutes | UTXO peel-chain detection, Common-Input Ownership Heuristic (CIOH), CoinJoin guard. |
| **Scenario 3: Custom Batch Import** | Imported Dataset | Raw JSON Payload | ~2 minutes | Custom transaction ingestion, client-side validation, on-the-fly graph synthesis, report export. |

---

## 2. Ingestion Mode Transparency

Trazen strictly distinguishes data provenance across all views:

- 🟢 **LIVE CONSENSUS NODE (`LIVE_RPC`):** Live blockchain queries via Etherscan / Bitcoin Core archive nodes. If API keys are unconfigured, Trazen returns an explicit error banner and **never fabricates counterfeit live data**.
- 🔵 **IMPORTED DATASET (`IMPORTED_DATA`):** User-supplied transaction records parsed and normalized directly into the forensic graph engine.
- 🟣 **SYNTHETIC DEMO REPLAY (`DEMO_REPLAY`):** Fully documented, deterministic consensus archive fixtures designed for reproducible evaluation without external network dependencies.

---

## 3. Step-by-Step Evaluator Script

### Scenario 1: Lazarus Group Multi-Hop Mixer & Bridge Trace (ETH)

1. **Launch Trazen:**
   - Deployed URL: [https://trazen-kappa.vercel.app](https://trazen-kappa.vercel.app)
   - Or local environment: `http://localhost:3000`
2. **Review Problem Context on Landing Page:**
   - Observe the headline, the **Problem & Challenges** section (`#problem`), and the **10-Step Forensic Workflow**.
   - Click the prominent **"Start Investigation"** button in the Hero section or **"Run Demo"** in the top navigation.
3. **Open Investigation Form:**
   - In the Command Center, click **"New Investigation"**.
   - Click the quick-load button: **`Lazarus ETH Case`**.
   - Notice the form automatically populates:
     - Target: `0x098b716b8aaf21512996dc57eb0615e2383e2f96`
     - Network: `ETHEREUM (EVM)`
     - Type: `WALLET ADDRESS`
     - Expansion Depth: `4 HOPS`
     - Ingestion Source: `DEMO REPLAY`
4. **Initiate Investigation:**
   - Click **"START FORENSIC INVESTIGATION"**.
   - Watch the multi-stage cryptographic pipeline: Checksum -> Consensus Node -> Graph Expansion -> Anomaly Detection -> Evidence Sealing.
5. **Explore the Forensic Graph:**
   - The interactive Cytoscape.js canvas renders the multi-hop topology:
     - **Golden Hexagon:** Seed target ingress wallet (`0x098b...2f96`).
     - **Red Star Nodes:** Privacy mixing pools (Tornado Cash router and vault).
     - **Violet Diamonds:** Cross-chain liquidity bridges (Stargate cross-chain router).
     - **Cyan Rectangles:** Decentralized exchange liquidity pools (Uniswap V3).
   - Use the **Hop Depth Slider** (top toolbar) to expand from 1 hop to 4 hops.
   - Click any node to open the **Wallet Intelligence Drawer** showing balance, counterparty distribution, and entity provenance.
6. **Inspect Explainable Findings:**
   - Navigate to the **"Suspicious Findings"** tab.
   - Expand finding **`FINDING-ETH-001` (Tornado Cash Mixer Layering)**:
     - View the detection rule specification: `MIXER-PATTERN-01 (v2.1)`.
     - Read the **Detailed Explanation** and **Defensive Caveats & Limitations**.
     - Observe the supporting evidence vault references (`EV-ETH-001`, `EV-ETH-002`).
7. **Inspect 4-Dimensional Risk Assessment:**
   - Navigate to the **"Risk & Receivers"** tab.
   - Note the four independent dimensions:
     - **Risk Priority:** `92/100` (Critical triage urgency)
     - **Attribution Confidence:** `88/100` (High ratio of confirmed on-chain vectors)
     - **Known Risk Exposure:** `94/100` (Direct proximity to sanctioned mixer pools)
     - **Investigation Coverage:** `96/100` (Complete graph neighborhood)
   - Inspect the **Ranked Candidate Sinks** table displaying probable end-destination wallets.
8. **Verify Evidence Vault & Hash Chain:**
   - Navigate to the **"Evidence Vault"** tab.
   - Observe the list of cryptographically sealed records.
   - Note the unbroken SHA-256 hash chain: each record includes `previousRecordHash` and `recordHash`.
9. **Export Court-Ready Dossier:**
   - Click **"Export Dossier"** in the top action bar.
   - Review the modal preview containing the executive summary, findings matrix, candidate sinks, and statutory disclaimer.
   - Click **"Download Markdown"** to download `<case-id>-FORENSIC-REPORT.md`.

---

### Scenario 2: Ransomware UTXO Peel-Chain & Address Reuse (BTC)

1. **Initiate Bitcoin Case:**
   - Click **"New Investigation"** in the Command Center.
   - Click the quick-load button: **`Ransomware BTC Case`**.
   - Form parameters:
     - Target: `bc1qa5wkgaew2dkv56kfvj49j0av5nml45x9ek9hz6` (Bech32 SegWit)
     - Network: `BITCOIN (UTXO)`
     - Expansion Depth: `3 HOPS`
2. **Observe UTXO-Specific Forensics:**
   - The graph models distinct UTXO input/output legs without false 1-to-1 attribution.
   - Intermediate transaction nodes distinguish confirmed on-chain edges from heuristic links.
3. **Inspect Peel-Chain Detection:**
   - In **"Suspicious Findings"**, expand **`FINDING-BTC-001` (Systematic UTXO Peel-Chain)**:
     - Rule ID: `PEEL-CHAIN-01 (v2.1)`.
     - Observe the detected 4-hop peeling sequence forwarding 92% of funds per hop with rapid turnover.
     - Notice the **CoinJoin Safeguard**: CIOH is suppressed on collaborative multi-party transactions.

---

### Scenario 3: Custom Batch Transaction Import (JSON)

1. **Open Investigation Form:**
   - Click **"New Investigation"**.
   - Switch to the **"IMPORT DATASET"** tab (or paste into the target input).
   - Click **"Load Sample JSON Dataset"** (or paste the JSON snippet below).
2. **Sample JSON Payload:**
```json
{
  "investigationTitle": "Custom Exploit Drain Trace #4092",
  "network": "ETH",
  "seedTarget": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
  "transactions": [
    {
      "txHash": "0x4a9b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
      "from": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
      "to": "0x7F367CC41522cE07553e8435b2871214c770c1D1",
      "amount": 250.0,
      "currency": "ETH",
      "timestamp": "2026-11-20T14:30:00Z"
    },
    {
      "txHash": "0x5b0c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0c1d",
      "from": "0x7F367CC41522cE07553e8435b2871214c770c1D1",
      "to": "0x12D66f87A04A9E220743712cE6d9bB1B5616B8Fc",
      "amount": 249.5,
      "currency": "ETH",
      "timestamp": "2026-11-20T14:45:00Z"
    }
  ]
}
```
3. **Submit & Verify:**
   - Click **"IMPORT & ANALYZE TRANSACTIONS"**.
   - The platform parses, validates, and normalizes the records.
   - The graph renders the exact flow path, calculates 4D risk scores, fires detection rules, and seals the transactions into the SHA-256 evidence vault with provenance marked as `IMPORTED_DATA`.
