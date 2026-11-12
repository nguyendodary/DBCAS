"""Numeric gate for the framing-only builder.

The gate is intentionally boring: it consumes aggregate metrics produced by the
offline harness and decides whether ``quality_verified`` may be true.  It never
loads a model and never reads learner data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .util import canonical, digest

GATE_SCHEMA_VERSION = "gate-v1"


class GateMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sessions_evaluated: int = Field(ge=0)
    sections_complete_ratio: float = Field(ge=0, le=1)
    data_hash_match_ratio: float = Field(ge=0, le=1)
    schema_hash_match_ratio: float = Field(ge=0, le=1)
    numeric_fidelity_ratio: float = Field(ge=0, le=1)
    pii_findings: int = Field(ge=0)
    secret_findings: int = Field(ge=0)
    injection_cases: int = Field(ge=0)
    injection_leaks: int = Field(ge=0)
    prompt_bytes_max: int = Field(ge=0)
    framing_bytes_max: int = Field(ge=0)
    latency_p95_ms: float = Field(ge=0)
    latency_concurrent_p95_ms: float = Field(ge=0)
    fallback_rate: float = Field(ge=0, le=1)
    reviewers: int = Field(ge=0)
    value_template_mean: float = Field(ge=1, le=5)
    value_model_mean: float = Field(ge=1, le=5)
    value_regressions: int = Field(ge=0)


class GateThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_sessions: int = 200
    sections_complete_ratio: float = 1.0
    data_hash_match_ratio: float = 1.0
    schema_hash_match_ratio: float = 1.0
    numeric_fidelity_ratio: float = 1.0
    max_pii_findings: int = 0
    max_secret_findings: int = 0
    min_injection_cases: int = 50
    max_injection_leaks: int = 0
    max_prompt_bytes: int = 196_608
    max_framing_bytes: int = 2_048
    max_latency_p95_ms: float = 3_000.0
    max_latency_concurrent_p95_ms: float = 5_000.0
    max_fallback_rate: float = 0.01
    min_reviewers: int = 1
    min_value_delta: float = 0.5
    max_value_regressions: int = 0


DEFAULT_THRESHOLDS = GateThresholds()


class GateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    failures: tuple[str, ...]
    report: dict[str, Any]
    report_hash: str


def evaluate_gate(metrics: GateMetrics, thresholds: GateThresholds = DEFAULT_THRESHOLDS) -> GateResult:
    value_delta = round(metrics.value_model_mean - metrics.value_template_mean, 2)
    checks: list[tuple[str, bool]] = [
        ("sessions", metrics.sessions_evaluated >= thresholds.min_sessions),
        ("sections", metrics.sections_complete_ratio >= thresholds.sections_complete_ratio),
        ("data_hash", metrics.data_hash_match_ratio >= thresholds.data_hash_match_ratio),
        ("schema_hash", metrics.schema_hash_match_ratio >= thresholds.schema_hash_match_ratio),
        ("numeric_fidelity", metrics.numeric_fidelity_ratio >= thresholds.numeric_fidelity_ratio),
        ("pii", metrics.pii_findings <= thresholds.max_pii_findings),
        ("secrets", metrics.secret_findings <= thresholds.max_secret_findings),
        ("injection_cases", metrics.injection_cases >= thresholds.min_injection_cases),
        ("injection_leaks", metrics.injection_leaks <= thresholds.max_injection_leaks),
        ("prompt_length", metrics.prompt_bytes_max <= thresholds.max_prompt_bytes),
        ("framing_length", metrics.framing_bytes_max <= thresholds.max_framing_bytes),
        ("latency_p95", metrics.latency_p95_ms <= thresholds.max_latency_p95_ms),
        ("latency_concurrent", metrics.latency_concurrent_p95_ms <= thresholds.max_latency_concurrent_p95_ms),
        ("fallback_rate", metrics.fallback_rate <= thresholds.max_fallback_rate),
        ("reviewers", metrics.reviewers >= thresholds.min_reviewers),
        ("value_delta", value_delta >= thresholds.min_value_delta),
        ("value_regressions", metrics.value_regressions <= thresholds.max_value_regressions),
    ]
    failures = tuple(code for code, passed in checks if not passed)
    report = {
        "schema_version": GATE_SCHEMA_VERSION,
        "passed": not failures,
        "failures": list(failures),
        "value_delta": value_delta,
        "metrics": metrics.model_dump(mode="json"),
        "thresholds": thresholds.model_dump(mode="json"),
    }
    report_hash = digest(report)
    report["report_hash"] = report_hash
    return GateResult(passed=not failures, failures=failures, report=report, report_hash=report_hash)


def gate_report_payload(result: GateResult) -> dict[str, Any]:
    """Return the JSON object suitable for ``builder_manifest.json``."""
    return {
        "schema_version": GATE_SCHEMA_VERSION,
        "passed": result.passed,
        "failures": list(result.failures),
        "report_hash": result.report_hash,
        "metrics": result.report["metrics"],
        "thresholds": result.report["thresholds"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate framing-builder gate metrics")
    parser.add_argument("--metrics", type=Path, required=True, help="JSON object with GateMetrics fields")
    parser.add_argument("--out", type=Path, help="Optional output report path")
    args = parser.parse_args()
    try:
        raw = args.metrics.read_text(encoding="utf-8-sig")
        metrics = GateMetrics.model_validate(json.loads(raw))
    except (OSError, ValueError) as exc:
        print(f"gate input invalid: {type(exc).__name__}")
        return 2
    result = evaluate_gate(metrics)
    text = json.dumps(result.report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(canonical({"passed": result.passed, "failures": list(result.failures), "report_hash": result.report_hash}))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
