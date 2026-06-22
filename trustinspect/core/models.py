from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class Classification(str, Enum):
    SAFE = "SAFE"
    POSSIBLE = "POSSIBLE VULNERABILITY"
    VULNERABILITY = "VULNERABILITY"
    ERROR = "ERROR"


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceType(str, Enum):
    PROMPT = "prompt"
    RESPONSE = "response"
    SCREENSHOT = "screenshot"
    HTTP_TRACE = "http_trace"
    RETRIEVED_CONTEXT = "retrieved_context"
    TOOL_CALL = "tool_call"
    TARGET_METADATA = "target_metadata"
    LOG = "log"
    DOM_SNAPSHOT = "dom_snapshot"


@dataclass
class Target:
    id: str
    name: str
    url: Optional[str] = None
    target_type: str = "web-ui"
    owner: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCase:
    id: str
    name: str
    category: str
    objective: str
    payload: str
    expected_behavior: Optional[str] = None
    failure_indicators: List[Any] = field(default_factory=list)
    mappings: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceItem:
    id: str
    evidence_type: EvidenceType
    value: Any
    created_at: str = field(default_factory=now_utc)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Observation:
    id: str
    target: Target
    test_case: TestCase
    classification: Classification
    confidence: float
    evidence: List[EvidenceItem]
    analyzer: str = "unknown"
    rationale: str = ""
    created_at: str = field(default_factory=now_utc)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    id: str
    title: str
    severity: Severity
    confidence: float
    trustworthiness_dimension: str
    observation_id: str
    description: str
    impact: str
    remediation: str
    evidence: List[EvidenceItem]
    mappings: Dict[str, List[str]] = field(default_factory=dict)
    reproducibility: str = "Re-run the same test case against the same target profile."
    created_at: str = field(default_factory=now_utc)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Assessment:
    id: str
    name: str
    target: Target
    observations: List[Observation] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    started_at: str = field(default_factory=now_utc)
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self) -> None:
        self.completed_at = now_utc()

    def to_dict(self) -> Dict[str, Any]:
        def convert(obj):
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, "__dataclass_fields__"):
                return {k: convert(v) for k, v in asdict(obj).items()}
            if isinstance(obj, list):
                return [convert(v) for v in obj]
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            return obj

        return convert(self)
