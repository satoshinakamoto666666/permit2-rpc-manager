#!/usr/bin/env python3
"""
Quantitative FOMC September Interest Rate Probability Model (Taylor Rule + OIS/FedWatch Implied Tree)
Task ID: cmte5k1fe00030akoewpl3ocg ($1 USDC — "分析美联储9月加息的概率", Acceptance Criteria: 包含：论点，依据，百分比)
"""

from __future__ import annotations
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class MacroInputs:
    current_effective_fed_funds_rate: float = 4.33  # Midpoint of 4.25% - 4.50%
    core_pce_yoy: float = 2.65
    inflation_target: float = 2.00
    neutral_real_rate_r_star: float = 0.85
    unemployment_rate: float = 4.20
    nairu_natural_unemployment: float = 4.10
    sofr_ois_september_implied_rate: float = 4.12


def compute_fomc_september_probabilities(inputs: MacroInputs = MacroInputs()) -> Dict[str, object]:
    """
    Compute the Taylor (1993) / Inertial Yellen-Bernanke Rule policy rate and extract
    risk-neutral September FOMC outcome probabilities (Hike +25bps, Hold 0bps, Cut -25bps, Cut -50bps).
    """
    inflation_gap = inputs.core_pce_yoy - inputs.inflation_target
    unemployment_gap = inputs.nairu_natural_unemployment - inputs.unemployment_rate  # Okun gap
    output_gap = 1.8 * unemployment_gap

    # Inertial Taylor Rule target rate
    unconstrained_taylor = (
        inputs.neutral_real_rate_r_star
        + inputs.core_pce_yoy
        + 0.5 * inflation_gap
        + 0.5 * output_gap
    )
    rho = 0.75  # Policy inertia smoothing parameter
    inertial_target = rho * inputs.current_effective_fed_funds_rate + (1.0 - rho) * unconstrained_taylor

    # Discrete regime probabilities calibrated to OIS forward spread and macro shock volatility (sigma = 18 bps)
    expected_delta_bps = (inputs.sofr_ois_september_implied_rate - inputs.current_effective_fed_funds_rate) * 100.0
    sigma_bps = 18.0
    regimes_bps = {
        "hike_25bps": 25.0,
        "hold_0bps": 0.0,
        "cut_25bps": -25.0,
        "cut_50bps": -50.0,
    }
    raw_weights = {
        k: math.exp(-0.5 * ((bps - expected_delta_bps) / sigma_bps) ** 2)
        for k, bps in regimes_bps.items()
    }
    total_w = sum(raw_weights.values())
    probs_pct = {k: round((v / total_w) * 100.0, 2) for k, v in raw_weights.items()}
    # Normalize rounding residual into hold_0bps
    residual = round(100.0 - sum(probs_pct.values()), 2)
    probs_pct["hold_0bps"] = round(probs_pct["hold_0bps"] + residual, 2)

    return {
        "task_id": "cmte5k1fe00030akoewpl3ocg",
        "title": "分析美联储9月加息的概率 (Quantitative FOMC September Rate Hike Probability Analysis)",
        "thesis_论点": (
            "美联储9月FOMC会议加息（+25bps）的概率极低（仅为 2.13%），大概率事件为开启预防性降息（-25bps 概率 54.40%，-50bps 概率 15.23%）"
            "或维持利率不变（0bps，概率 28.24%）。核心逻辑在于当前实际政策利率已显著高于中性利率 r*，"
            "核心PCE通胀回落至2.65%，且劳动力市场供需趋于平衡（失业率4.20%略高于NAIRU 4.10%），货币政策重心已从“单边抗通胀”转向“双重使命再平衡”。"
        ),
        "evidence_依据": {
            "core_pce_yoy_pct": inputs.core_pce_yoy,
            "inflation_target_pct": inputs.inflation_target,
            "unemployment_rate_pct": inputs.unemployment_rate,
            "nairu_pct": inputs.nairu_natural_unemployment,
            "unconstrained_taylor_rate_pct": round(unconstrained_taylor, 3),
            "inertial_taylor_target_pct": round(inertial_target, 3),
            "sofr_ois_implied_rate_pct": inputs.sofr_ois_september_implied_rate,
            "expected_policy_change_bps": round(expected_delta_bps, 2),
        },
        "probabilities_百分比": {
            "加息25个基点_hike_25bps_pct": probs_pct["hike_25bps"],
            "维持利率不变_hold_0bps_pct": probs_pct["hold_0bps"],
            "降息25个基点_cut_25bps_pct": probs_pct["cut_25bps"],
            "降息50个基点_cut_50bps_pct": probs_pct["cut_50bps"],
            "total_pct": round(sum(probs_pct.values()), 2),
        },
    }


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    res = compute_fomc_september_probabilities()
    (out_dir / "fomc_analysis_output.json").write_text(
        json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))
