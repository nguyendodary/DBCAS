"""Gate and manifest contract tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.framing.gate import (
    GateMetrics, evaluate_gate, gate_report_payload, GateThresholds,
)
from app.services.framing.manifest import (
    BuilderManifest, ManifestEnvironment, manifest_json_schema, validate_manifest,
)


def good_metrics() -> GateMetrics:
    return GateMetrics(
        sessions_evaluated=200,
        sections_complete_ratio=1.0,
        data_hash_match_ratio=1.0,
        schema_hash_match_ratio=1.0,
        numeric_fidelity_ratio=1.0,
        pii_findings=0,
        secret_findings=0,
        injection_cases=60,
        injection_leaks=0,
        prompt_bytes_max=123_313,
        framing_bytes_max=1_800,
        latency_p95_ms=2_500.0,
        latency_concurrent_p95_ms=4_200.0,
        fallback_rate=0.0,
        reviewers=2,
        value_template_mean=4.0,
        value_model_mean=4.6,
        value_regressions=0,
    )


def environment() -> ManifestEnvironment:
    return ManifestEnvironment(
        cpu="test-cpu", threads=4, ram_bytes=8_000_000_000,
        container_mem_limit_bytes=4_000_000_000, python="3.13", torch="2.10.0",
        transformers="4.57.6",
    )


def template_manifest(**overrides) -> dict:
    result = evaluate_gate(good_metrics())
    values = {
        "schema_version": "1.0",
        "builder_version": "framing-template-v1",
        "builder_kind": "template",
        "dataset_hash": "a" * 64,
        "template_hash": "b" * 64,
        "schema_hash": "c" * 64,
        "quality_verified": True,
        "gate": gate_report_payload(result),
        "environment": environment().model_dump(),
        "created_at": "2026-11-12T00:00:00+00:00",
    }
    values.update(overrides)
    return values


def test_gate_passes_only_when_every_threshold_passes():
    result = evaluate_gate(good_metrics())
    assert result.passed
    assert result.failures == ()
    assert len(result.report_hash) == 64
    assert result.report["report_hash"] == result.report_hash


@pytest.mark.parametrize(
    ("update", "failure"),
    [
        ({"sessions_evaluated": 199}, "sessions"),
        ({"sections_complete_ratio": 0.99}, "sections"),
        ({"data_hash_match_ratio": 0.99}, "data_hash"),
        ({"schema_hash_match_ratio": 0.99}, "schema_hash"),
        ({"numeric_fidelity_ratio": 0.99}, "numeric_fidelity"),
        ({"pii_findings": 1}, "pii"),
        ({"secret_findings": 1}, "secrets"),
        ({"injection_cases": 49}, "injection_cases"),
        ({"injection_leaks": 1}, "injection_leaks"),
        ({"prompt_bytes_max": 196_609}, "prompt_length"),
        ({"framing_bytes_max": 2_049}, "framing_length"),
        ({"latency_p95_ms": 3_001.0}, "latency_p95"),
        ({"latency_concurrent_p95_ms": 5_001.0}, "latency_concurrent"),
        ({"fallback_rate": 0.02}, "fallback_rate"),
        ({"reviewers": 0}, "reviewers"),
        ({"value_model_mean": 4.4}, "value_delta"),
        ({"value_regressions": 1}, "value_regressions"),
    ],
)
def test_each_gate_failure_is_reported(update, failure):
    result = evaluate_gate(good_metrics().model_copy(update=update))
    assert not result.passed
    assert failure in result.failures


def test_gate_report_hash_changes_with_metrics():
    first = evaluate_gate(good_metrics())
    second = evaluate_gate(good_metrics().model_copy(update={"latency_p95_ms": 2_400.0}))
    assert first.report_hash != second.report_hash


def test_template_manifest_with_verified_gate_is_valid():
    manifest = validate_manifest(template_manifest())
    assert manifest.quality_verified
    assert manifest.builder_kind == "template"
    assert manifest.gate is not None and manifest.gate.passed


def test_verified_manifest_requires_a_gate():
    payload = template_manifest()
    payload.pop("gate")
    with pytest.raises(ValidationError):
        validate_manifest(payload)


def test_gate_report_tampering_is_rejected():
    payload = template_manifest()
    tampered = copy.deepcopy(payload)
    tampered["gate"]["report_hash"] = "d" * 64
    with pytest.raises(ValidationError):
        validate_manifest(tampered)
    tampered = copy.deepcopy(payload)
    tampered["gate"]["metrics"]["latency_p95_ms"] = 2_000.0
    with pytest.raises(ValidationError):
        validate_manifest(tampered)


def test_model_manifest_requires_model_identity():
    payload = template_manifest(builder_kind="model", builder_version="framing-model-v1")
    with pytest.raises(ValidationError):
        validate_manifest(payload)
    payload.update({
        "base_model": "Qwen/Qwen2.5-0.5B-Instruct",
        "model_format": "int8",
        "model_hash": "e" * 64,
    })
    manifest = validate_manifest(payload)
    assert manifest.model_format == "int8"


def test_manifest_rejects_extra_fields_and_bad_hashes():
    payload = template_manifest(extra="not allowed")
    with pytest.raises(ValidationError):
        validate_manifest(payload)
    payload = template_manifest(dataset_hash="short")
    with pytest.raises(ValidationError):
        validate_manifest(payload)


def test_manifest_json_schema_is_committed_and_has_required_fields():
    schema = manifest_json_schema()
    assert schema.get("$schema", "").endswith("2020-12/schema")
    required = set(schema["required"])
    assert {"builder_version", "builder_kind", "dataset_hash", "quality_verified", "environment"} <= required
    committed = Path(__file__).resolve().parents[1] / "app" / "services" / "framing" / "data" / "builder_manifest.schema.json"
    loaded = json.loads(committed.read_text(encoding="utf-8"))
    assert loaded.get("$schema", "").endswith("2020-12/schema")
    assert {"builder_version", "builder_kind", "dataset_hash", "quality_verified", "environment"} <= set(loaded["required"])
