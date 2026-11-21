"""Fixed-operation, capability-scoped broker wire schema (version 1).

The schema deliberately has no image, Docker argument, mount, host path or SQL
text field. Unknown fields are rejected rather than ignored.
"""
import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_OPAQUE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BrokerLimits(StrictModel):
    wall_ms: int = Field(default=5000, ge=1, le=5000)


class BrokerRequest(StrictModel):
    version: int = Field(default=1, ge=1, le=1)
    operation: str = Field(pattern="^(create|run|destroy)$")
    request_id: UUID
    dataset_id: str = Field(pattern="^[A-Za-z0-9_-]{1,64}$")
    dataset_digest: str = Field(pattern=_SHA256)
    script_hash: str = Field(pattern=_SHA256)
    mode: str = Field(pattern="^read_only$")
    limits: BrokerLimits
    requester: str = Field(pattern=_OPAQUE)
    capability: str = Field(min_length=16, max_length=4096)


class BrokerResponse(StrictModel):
    request_id: UUID
    operation: str
    status: str = "stub"
    executed: bool = False
    result_class: str = "no_execution"
    duration_ms: int = 0


class BrokerAuditRecord(StrictModel):
    request_id: UUID
    operation: str
    outcome: str
    dataset_id: str
    script_hash: str
    requester: str
    policy_version: int
    result_class: str
    duration_ms: int
    retention_days: int
