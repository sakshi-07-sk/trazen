"""Clearly-identified synthetic behavioural dataset generator for ML benchmarking."""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

from forensics.schemas.output import WalletFeatureVector


def generate_synthetic_ml_dataset(
    n_samples: int = 240,
    random_state: int = 42,
) -> Tuple[Dict[str, WalletFeatureVector], Dict[str, int], Dict[str, str]]:
    """Generate a reproducible synthetic wallet cohort with explicit archetype provenance.

    Returns (features_by_addr, binary_pattern_label_by_addr, archetype_by_addr).
    Label 1 = synthetic anomalous/suspicious archetype (peel_hop, smurf_splitter, mixer_relay, dormant_burst).
    Label 0 = synthetic benign archetype (retail_user, exchange_hot_wallet, payroll_distributor).
    NOTE: Synthetic demo data only — never represents real criminality labels.
    """
    rng = np.random.default_rng(random_state)
    features: Dict[str, WalletFeatureVector] = {}
    labels: Dict[str, int] = {}
    archetypes: Dict[str, str] = {}

    archetype_specs = [
        ("retail_user", 0, 0.30),
        ("exchange_hot_wallet", 0, 0.15),
        ("payroll_distributor", 0, 0.15),
        ("peel_hop", 1, 0.12),
        ("smurf_splitter", 1, 0.12),
        ("mixer_relay", 1, 0.08),
        ("dormant_burst", 1, 0.08),
    ]

    idx = 0
    for arch, label, frac in archetype_specs:
        count = max(4, int(round(n_samples * frac)))
        for _ in range(count):
            idx += 1
            addr = f"0xSYNTH_{arch.upper()}_{idx:04d}"

            if arch == "retail_user":
                in_c = int(rng.integers(1, 6))
                out_c = int(rng.integers(1, 6))
                u_send = max(1, int(rng.integers(1, in_c + 1)))
                u_recv = max(1, int(rng.integers(1, out_c + 1)))
                inflow = float(rng.uniform(0.5, 10.0))
                outflow = float(inflow * rng.uniform(0.3, 0.9))
                med_val = float(rng.uniform(0.1, 2.0))
                cv = float(rng.uniform(0.35, 1.1))
                vel = float(rng.uniform(0.2, 2.5))
                dorm = float(rng.uniform(3600, 86400 * 10))
                svc_exp = float(rng.uniform(0.2, 0.8))
                timing_std = float(rng.uniform(5000, 80000))
                contract_r = float(rng.uniform(0.1, 0.6))
            elif arch == "exchange_hot_wallet":
                in_c = int(rng.integers(20, 60))
                out_c = int(rng.integers(20, 60))
                u_send = int(in_c * rng.uniform(0.6, 0.95))
                u_recv = int(out_c * rng.uniform(0.6, 0.95))
                inflow = float(rng.uniform(100, 1000))
                outflow = float(inflow * rng.uniform(0.85, 1.05))
                med_val = float(rng.uniform(1.0, 20.0))
                cv = float(rng.uniform(0.6, 1.8))
                vel = float(rng.uniform(25.0, 120.0))
                dorm = float(rng.uniform(60, 1800))
                svc_exp = float(rng.uniform(0.5, 0.95))
                timing_std = float(rng.uniform(100, 1200))
                contract_r = float(rng.uniform(0.05, 0.3))
            elif arch == "payroll_distributor":
                in_c = int(rng.integers(1, 3))
                out_c = int(rng.integers(8, 25))
                u_send = 1
                u_recv = out_c
                inflow = float(rng.uniform(20, 80))
                outflow = float(inflow * rng.uniform(0.92, 0.99))
                med_val = float(outflow / max(1, out_c))
                cv = float(rng.uniform(0.02, 0.12))
                vel = float(rng.uniform(5.0, 20.0))
                dorm = float(rng.uniform(86400 * 25, 86400 * 32))
                svc_exp = float(rng.uniform(0.6, 1.0))
                timing_std = float(rng.uniform(10, 300))
                contract_r = 0.0
            elif arch == "peel_hop":
                in_c = 1
                out_c = 2
                u_send = 1
                u_recv = 2
                inflow = float(rng.uniform(20, 150))
                outflow = float(inflow * rng.uniform(0.95, 0.995))
                med_val = float(inflow * rng.uniform(0.45, 0.55))
                cv = float(rng.uniform(0.75, 1.15))
                vel = float(rng.uniform(15.0, 60.0))
                dorm = float(rng.uniform(120, 1800))
                svc_exp = 0.0
                timing_std = float(rng.uniform(10, 300))
                contract_r = 0.0
            elif arch == "smurf_splitter":
                in_c = int(rng.integers(1, 3))
                out_c = int(rng.integers(6, 15))
                u_send = 1
                u_recv = out_c
                inflow = float(rng.uniform(20, 60))
                outflow = float(inflow * rng.uniform(0.92, 0.99))
                med_val = float(rng.uniform(3.8, 4.9))
                cv = float(rng.uniform(0.01, 0.10))
                vel = float(rng.uniform(40.0, 150.0))
                dorm = float(rng.uniform(60, 600))
                svc_exp = 0.0
                timing_std = float(rng.uniform(15, 180))
                contract_r = 0.0
            elif arch == "mixer_relay":
                in_c = int(rng.integers(6, 15))
                out_c = int(rng.integers(6, 15))
                u_send = in_c
                u_recv = out_c
                inflow = float(in_c * 1.0)
                outflow = float(out_c * 0.99)
                med_val = 1.0
                cv = float(rng.uniform(0.0, 0.03))
                vel = float(rng.uniform(12.0, 48.0))
                dorm = float(rng.uniform(300, 3600))
                svc_exp = float(rng.uniform(0.1, 0.35))
                timing_std = float(rng.uniform(60, 600))
                contract_r = float(rng.uniform(0.7, 1.0))
            else:  # dormant_burst
                in_c = 1
                out_c = int(rng.integers(4, 10))
                u_send = 1
                u_recv = out_c
                inflow = float(rng.uniform(10, 100))
                outflow = float(inflow * rng.uniform(0.9, 0.99))
                med_val = float(outflow / max(1, out_c))
                cv = float(rng.uniform(0.1, 0.4))
                vel = float(rng.uniform(10.0, 40.0))
                dorm = float(rng.uniform(86400 * 60, 86400 * 365))
                svc_exp = 0.0
                timing_std = float(rng.uniform(30, 600))
                contract_r = 0.0

            net_flow = inflow - outflow
            res_ratio = max(0.0, net_flow / max(inflow, 1e-9))
            features[addr] = WalletFeatureVector(
                address=addr,
                chain="ethereum",
                inbound_tx_count=in_c,
                outbound_tx_count=out_c,
                total_tx_count=in_c + out_c,
                unique_senders=u_send,
                unique_receivers=u_recv,
                unique_counterparties=u_send + u_recv,
                total_inflow=round(inflow, 4),
                total_outflow=round(outflow, 4),
                net_flow=round(net_flow, 4),
                residual_balance_ratio=round(res_ratio, 4),
                median_tx_value=round(med_val, 4),
                mean_tx_value=round(med_val * 1.05, 4),
                tx_value_cv=round(cv, 4),
                tx_velocity_per_day=round(vel, 4),
                dormancy_period_seconds=round(dorm, 2),
                fan_in_ratio=round(u_send / max(1, in_c), 4),
                fan_out_ratio=round(u_recv / max(1, out_c), 4),
                known_service_exposure=round(svc_exp, 4),
                known_risk_service_exposure=0.0,
                bridge_interaction_count=0,
                tx_timing_variation_seconds=round(timing_std, 2),
                utxo_avg_inputs=0.0,
                utxo_avg_outputs=0.0,
                address_reuse_count=0,
                contract_interaction_ratio=round(contract_r, 4),
                token_transfer_ratio=0.0,
            )
            labels[addr] = label
            archetypes[addr] = arch

    return features, labels, archetypes
