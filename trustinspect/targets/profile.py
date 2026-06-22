from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import yaml


def _slugify(value: str) -> str:
    value = value or "target"
    return "".join(c.lower() if c.isalnum() else "_" for c in value).strip("_") or "target"


@dataclass
class TargetCapabilityProfile:
    """
    Declared and inferred profile of an AI target.

    This is not system-prompt extraction. It is a benign capability profile built
    from what the target says about itself and from tester-provided context.
    """

    target_id: str
    name: str
    url: Optional[str] = None
    target_type: str = "web-ui"
    declared_identity: str = ""
    declared_capabilities: List[str] = field(default_factory=list)
    declared_boundaries: List[str] = field(default_factory=list)
    inferred_domain: str = "general"
    interaction_style: str = "assistant"
    likely_sensitive_assets: List[str] = field(default_factory=list)
    selected_risk_areas: List[str] = field(default_factory=list)
    profiling_prompt: str = ""
    profiling_response: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TargetCapabilityProfile":
        return cls(
            target_id=str(data.get("target_id") or data.get("id") or "target"),
            name=str(data.get("name") or "Target"),
            url=data.get("url"),
            target_type=str(data.get("target_type") or "web-ui"),
            declared_identity=str(data.get("declared_identity") or ""),
            declared_capabilities=list(data.get("declared_capabilities") or []),
            declared_boundaries=list(data.get("declared_boundaries") or []),
            inferred_domain=str(data.get("inferred_domain") or "general"),
            interaction_style=str(data.get("interaction_style") or "assistant"),
            likely_sensitive_assets=list(data.get("likely_sensitive_assets") or []),
            selected_risk_areas=list(data.get("selected_risk_areas") or []),
            profiling_prompt=str(data.get("profiling_prompt") or ""),
            profiling_response=str(data.get("profiling_response") or ""),
            metadata=dict(data.get("metadata") or {}),
        )

    @classmethod
    def minimal(cls, url: str, name: Optional[str] = None) -> "TargetCapabilityProfile":
        parsed = urlparse(url)
        host = parsed.hostname or url
        return cls(target_id=_slugify(host), name=name or host, url=url)


def save_target_profile(profile: TargetCapabilityProfile, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(profile.to_dict(), sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def load_target_profile(path: str | Path) -> TargetCapabilityProfile:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return TargetCapabilityProfile.from_dict(data)
