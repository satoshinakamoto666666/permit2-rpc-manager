"""
Commercial Zero Bureaucracy KPI Framework Engine (Platform-Ready SaaS Asset)
============================================================================
Implements a configurable, industry-agnostic Zero Bureaucracy KPI Library with
12 standardized KPIs across 5 dimensions (Speed, Effort, Automation, Duplication,
Friction), 0-100 normalization scoring logic, per-client target overrides,
weighted composite index calculation, and Excel-ready CSV/JSON table export.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ZeroBureaucracyKPI:
    kpi_id: str
    dimension: str  # Speed, Effort, Automation, Duplication, Friction
    name: str
    definition: str
    formula: str
    unit: str
    polarity: str  # "lower_is_better" or "higher_is_better"
    benchmark_best: float
    benchmark_median: float
    benchmark_laggard: float
    default_target: float
    default_weight: float


CORE_KPI_LIBRARY: List[ZeroBureaucracyKPI] = [
    # Dimension 1: Speed
    ZeroBureaucracyKPI(
        kpi_id="ZB-SPD-01",
        dimension="Speed",
        name="Decision Cycle Latency",
        definition="Elapsed time from initial request submission to final actionable approval.",
        formula="SUM(Approval_Timestamp - Submission_Timestamp) / Total_Decisions",
        unit="hours",
        polarity="lower_is_better",
        benchmark_best=2.0,
        benchmark_median=24.0,
        benchmark_laggard=120.0,
        default_target=4.0,
        default_weight=0.10,
    ),
    ZeroBureaucracyKPI(
        kpi_id="ZB-SPD-02",
        dimension="Speed",
        name="Value-Add Time Ratio (Process Efficiency)",
        definition="Percentage of total end-to-end lead time spent on active execution versus waiting in queues.",
        formula="(Active_Processing_Hours / Total_Lead_Time_Hours) * 100",
        unit="percentage",
        polarity="higher_is_better",
        benchmark_best=65.0,
        benchmark_median=25.0,
        benchmark_laggard=5.0,
        default_target=55.0,
        default_weight=0.08,
    ),
    # Dimension 2: Effort
    ZeroBureaucracyKPI(
        kpi_id="ZB-EFF-01",
        dimension="Effort",
        name="Approval Layer Depth",
        definition="Average number of distinct sign-offs required to authorize a standard operational workflow.",
        formula="SUM(Signoff_Count_Per_Workflow) / Total_Completed_Workflows",
        unit="count",
        polarity="lower_is_better",
        benchmark_best=1.0,
        benchmark_median=3.0,
        benchmark_laggard=7.0,
        default_target=1.5,
        default_weight=0.10,
    ),
    ZeroBureaucracyKPI(
        kpi_id="ZB-EFF-02",
        dimension="Effort",
        name="Compliance & Reporting Overhead Share",
        definition="Proportion of total productive staff hours consumed by internal status reporting and form completion.",
        formula="(Internal_Reporting_Hours / Total_Worked_Hours) * 100",
        unit="percentage",
        polarity="lower_is_better",
        benchmark_best=4.0,
        benchmark_median=15.0,
        benchmark_laggard=35.0,
        default_target=6.0,
        default_weight=0.08,
    ),
    ZeroBureaucracyKPI(
        kpi_id="ZB-EFF-03",
        dimension="Effort",
        name="Mandatory Input Fields per Transaction",
        definition="Average number of manual data fields a user must populate to initiate a standard workflow.",
        formula="SUM(Required_Manual_Fields) / Total_Workflow_Templates",
        unit="fields",
        polarity="lower_is_better",
        benchmark_best=3.0,
        benchmark_median=12.0,
        benchmark_laggard=30.0,
        default_target=5.0,
        default_weight=0.07,
    ),
    # Dimension 3: Automation
    ZeroBureaucracyKPI(
        kpi_id="ZB-AUT-01",
        dimension="Automation",
        name="Straight-Through Processing (STP) Rate",
        definition="Percentage of workflows completed end-to-end without manual human intervention.",
        formula="(Zero_Touch_Workflows / Total_Workflows) * 100",
        unit="percentage",
        polarity="higher_is_better",
        benchmark_best=85.0,
        benchmark_median=40.0,
        benchmark_laggard=10.0,
        default_target=75.0,
        default_weight=0.12,
    ),
    ZeroBureaucracyKPI(
        kpi_id="ZB-AUT-02",
        dimension="Automation",
        name="Rule-Based Auto-Approval Coverage",
        definition="Percentage of low-risk requests automatically adjudicated by deterministic policy rules.",
        formula="(Auto_Adjudicated_Requests / Total_Eligible_Requests) * 100",
        unit="percentage",
        polarity="higher_is_better",
        benchmark_best=90.0,
        benchmark_median=45.0,
        benchmark_laggard=5.0,
        default_target=80.0,
        default_weight=0.08,
    ),
    # Dimension 4: Duplication
    ZeroBureaucracyKPI(
        kpi_id="ZB-DUP-01",
        dimension="Duplication",
        name="Redundant Data Entry Rate",
        definition="Percentage of input fields requesting data that already exists in a connected system of record.",
        formula="(Duplicate_Fields_Captured / Total_Fields_Captured) * 100",
        unit="percentage",
        polarity="lower_is_better",
        benchmark_best=0.0,
        benchmark_median=18.0,
        benchmark_laggard=45.0,
        default_target=2.0,
        default_weight=0.09,
    ),
    ZeroBureaucracyKPI(
        kpi_id="ZB-DUP-02",
        dimension="Duplication",
        name="Cross-Unit Handoff Count",
        definition="Average number of organizational handoffs before a workflow reaches completion.",
        formula="SUM(Organizational_Transfers) / Total_Workflows",
        unit="handoffs",
        polarity="lower_is_better",
        benchmark_best=1.0,
        benchmark_median=3.5,
        benchmark_laggard=8.0,
        default_target=1.5,
        default_weight=0.08,
    ),
    # Dimension 5: Friction
    ZeroBureaucracyKPI(
        kpi_id="ZB-FRC-01",
        dimension="Friction",
        name="First-Time-Right Submission Rate",
        definition="Percentage of submissions accepted on the first pass without rework or clarification loops.",
        formula="((Total_Submissions - Returned_Submissions) / Total_Submissions) * 100",
        unit="percentage",
        polarity="higher_is_better",
        benchmark_best=96.0,
        benchmark_median=78.0,
        benchmark_laggard=50.0,
        default_target=92.0,
        default_weight=0.08,
    ),
    ZeroBureaucracyKPI(
        kpi_id="ZB-FRC-02",
        dimension="Friction",
        name="Exception & Escalation Frequency",
        definition="Percentage of standard transactions diverted into manual exception-handling queues.",
        formula="(Escalated_Transactions / Total_Transactions) * 100",
        unit="percentage",
        polarity="lower_is_better",
        benchmark_best=2.0,
        benchmark_median=12.0,
        benchmark_laggard=30.0,
        default_target=4.0,
        default_weight=0.06,
    ),
    ZeroBureaucracyKPI(
        kpi_id="ZB-FRC-03",
        dimension="Friction",
        name="Policy & Rule Obscurity Abandonment Rate",
        definition="Percentage of initiated workflows abandoned by users prior to submission due to process complexity.",
        formula="(Abandoned_Draft_Workflows / Total_Initiated_Workflows) * 100",
        unit="percentage",
        polarity="lower_is_better",
        benchmark_best=1.5,
        benchmark_median=10.0,
        benchmark_laggard=25.0,
        default_target=3.0,
        default_weight=0.06,
    ),
]


class ZeroBureaucracyScoringEngine:
    """Platform-configurable 0-100 KPI normalization and composite scoring engine."""

    def __init__(self, kpis: Optional[List[ZeroBureaucracyKPI]] = None) -> None:
        self.kpis = list(kpis or CORE_KPI_LIBRARY)

    @staticmethod
    def normalize_score(
        actual: float,
        best: float,
        laggard: float,
        polarity: str,
        client_target: Optional[float] = None,
    ) -> float:
        """
        Normalizes a raw KPI value into a bounded [0.0, 100.0] score.
        If `client_target` is provided, achieving `client_target` maps to 85.0 points
        and achieving `best` maps to 100.0 points.
        """
        effective_best = best
        if client_target is not None:
            effective_best = best if polarity == "higher_is_better" and best >= client_target else (
                best if polarity == "lower_is_better" and best <= client_target else client_target
            )

        if polarity == "higher_is_better":
            denom = effective_best - laggard
            if denom <= 0:
                return 100.0 if actual >= effective_best else 0.0
            raw = ((actual - laggard) / denom) * 100.0
        else:
            denom = laggard - effective_best
            if denom <= 0:
                return 100.0 if actual <= effective_best else 0.0
            raw = ((laggard - actual) / denom) * 100.0

        return round(max(0.0, min(100.0, raw)), 2)

    def evaluate_client(
        self,
        observations: Dict[str, float],
        custom_targets: Optional[Dict[str, float]] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        custom_targets = custom_targets or {}
        custom_weights = custom_weights or {}

        total_weight = sum(custom_weights.get(k.kpi_id, k.default_weight) for k in self.kpis)
        dimension_scores: Dict[str, List[float]] = {}
        kpi_results: List[Dict[str, Any]] = []
        weighted_sum = 0.0

        for kpi in self.kpis:
            actual = observations.get(kpi.kpi_id, kpi.benchmark_median)
            target = custom_targets.get(kpi.kpi_id, kpi.default_target)
            weight = custom_weights.get(kpi.kpi_id, kpi.default_weight) / (total_weight or 1.0)
            score = self.normalize_score(
                actual=actual,
                best=kpi.benchmark_best,
                laggard=kpi.benchmark_laggard,
                polarity=kpi.polarity,
                client_target=target,
            )
            weighted_sum += score * weight
            dimension_scores.setdefault(kpi.dimension, []).append(score)
            kpi_results.append(
                {
                    "kpi_id": kpi.kpi_id,
                    "dimension": kpi.dimension,
                    "name": kpi.name,
                    "actual": actual,
                    "target": target,
                    "unit": kpi.unit,
                    "normalized_score_0_100": score,
                    "normalized_weight": round(weight, 4),
                    "weighted_contribution": round(score * weight, 2),
                }
            )

        dim_summary = {
            dim: round(sum(scores) / len(scores), 2) for dim, scores in dimension_scores.items()
        }
        composite = round(weighted_sum, 2)
        maturity_tier = (
            "ZERO_BUREAUCRACY_LEADER"
            if composite >= 80.0
            else "STREAMLINED_OPERATIONS"
            if composite >= 60.0
            else "MODERATE_FRICTION"
            if composite >= 40.0
            else "HIGH_BUREAUCRACY_DRAG"
        )

        return {
            "composite_zero_bureaucracy_index": composite,
            "maturity_tier": maturity_tier,
            "dimension_averages": dim_summary,
            "kpi_breakdown": kpi_results,
        }

    def export_excel_ready_csv(self) -> str:
        buf = io.StringIO()
        fieldnames = [
            "kpi_id",
            "dimension",
            "name",
            "definition",
            "formula",
            "unit",
            "polarity",
            "benchmark_best",
            "benchmark_median",
            "benchmark_laggard",
            "default_target",
            "default_weight",
        ]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for kpi in self.kpis:
            writer.writerow(asdict(kpi))
        return buf.getvalue()


if __name__ == "__main__":
    from pathlib import Path

    engine = ZeroBureaucracyScoringEngine()
    out_dir = Path(__file__).resolve().parent
    (out_dir / "zero_bureaucracy_kpi_table.csv").write_text(engine.export_excel_ready_csv(), encoding="utf-8")
