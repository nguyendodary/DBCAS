"""Draft manifest contract for a verified framing builder artifact.

A non-empty model path is not enough to enable the model.  The runtime should
require this manifest, a verified gate report and an explicit feature flag.
"""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .gate import GATE_SCHEMA_VERSION, GateMetrics, GateThresholds, evaluate_gate

MANIFEST_SCHEMA_VERSION = "1.0"
_HASH_RE = re.compile(r"^[a-f0-9]{64}$")
_VERSION_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,80}$")


class ManifestEnvironment(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    cpu: str = Field(min_length=1, max_length=120)
    threads: int = Field(ge=1, le=128)
    ram_bytes: int = Field(ge=0)
    container_mem_limit_bytes: int | None = Field(default=None, ge=0)
    python: str = Field(min_length=1, max_length=40)
    torch: str = Field(min_length=1, max_length=40)
    transformers: str = Field(min_length=1, max_length=40)


class GateReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["gate-v1"] = GATE_SCHEMA_VERSION
    passed: bool
    failures: tuple[str, ...] = ()
    report_hash: str
    metrics: GateMetrics
    thresholds: GateThresholds

    @model_validator(mode="after")
    def consistent(self) -> "GateReport":
        if not _HASH_RE.fullmatch(self.report_hash):
            raise ValueError("gate report_hash must be 64 lowercase hex characters")
        computed = evaluate_gate(self.metrics, self.thresholds)
        if computed.passed != self.passed:
            raise ValueError("gate passed flag does not match metrics")
        if computed.failures != self.failures:
            raise ValueError("gate failures do not match metrics")
        if computed.report_hash != self.report_hash:
            raise ValueError("gate report_hash does not match metrics")
        return self


class BuilderManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = MANIFEST_SCHEMA_VERSION
    builder_version: str
    builder_kind: Literal["template", "model"]
    base_model: str | None = Field(default=None, max_length=200)
    model_format: Literal["fp32", "bf16", "int8", "gguf"] | None = None
    model_hash: str | None = None
    adapter_hash: str | None = None
    dataset_hash: str
    template_hash: str
    schema_hash: str
    quality_verified: bool
    gate: GateReport | None = None
    environment: ManifestEnvironment
    created_at: datetime
    notes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def consistent(self) -> "BuilderManifest":
        if not _VERSION_RE.fullmatch(self.builder_version):
            raise ValueError("builder_version must be a lowercase identifier")
        for name in ("dataset_hash", "template_hash", "schema_hash"):
            if not _HASH_RE.fullmatch(getattr(self, name)):
                raise ValueError(f"{name} must be 64 lowercase hex characters")
        for name in ("model_hash", "adapter_hash"):
            value = getattr(self, name)
            if value is not None and not _HASH_RE.fullmatch(value):
                raise ValueError(f"{name} must be 64 lowercase hex characters")
        if self.builder_kind == "model":
            if not self.base_model or not self.model_format or not self.model_hash:
                raise ValueError("model manifests require base_model, model_format and model_hash")
        if self.quality_verified:
            if self.gate is None:
                raise ValueError("quality_verified requires a gate report")
            if not self.gate.passed or self.gate.failures:
                raise ValueError("quality_verified requires a passing gate")
        return self


def validate_manifest(value: dict) -> BuilderManifest:
    return BuilderManifest.model_validate(value)


def load_manifest(path: Path) -> BuilderManifest:
    return validate_manifest(json.loads(path.read_text(encoding="utf-8")))


def manifest_json_schema() -> dict:
    schema = BuilderManifest.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return schema
