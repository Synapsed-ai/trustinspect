from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .domain_taxonomy import get_domain_entry, infer_domain_from_text, infer_interaction_style




def _profile_to_plain_dict(profile):
    """Return a plain dict from dict/dataclass/pydantic/TargetCapabilityProfile objects."""
    if profile is None:
        return {}
    if isinstance(profile, dict):
        return profile
    if hasattr(profile, "to_dict") and callable(profile.to_dict):
        return profile.to_dict()
    if hasattr(profile, "model_dump") and callable(profile.model_dump):
        return profile.model_dump()
    try:
        import dataclasses
        if dataclasses.is_dataclass(profile):
            return dataclasses.asdict(profile)
    except Exception:
        pass
    if hasattr(profile, "__dict__"):
        return {
            k: v
            for k, v in vars(profile).items()
            if not k.startswith("_")
        }
    return {}

DEFAULT_RISK_AREAS = [
    "prompt_manipulation",
    "sensitive_data_exposure",
    "system_instruction_disclosure",
    "hidden_instruction_following",
    "unsafe_output_echo",
    "domain_boundary_escape",
    "resource_exhaustion",
]

ACTION_RISKS = ["unauthorized_action_request", "excessive_agency"]
RAG_RISKS = ["hidden_instruction_following", "context_manipulation"]


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, tuple):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        # Keep comma-separated support for simple CLI-generated profiles.
        if "," in value:
            return [v.strip() for v in value.split(",") if v.strip()]
        return [value.strip()] if value.strip() else []
    return [str(value).strip()] if str(value).strip() else []


def _unique(values: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        key = str(value).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(key)
    return result


def normalize_target_profile(raw_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a target profile so the dynamic engine can work across targets.

    The function is deliberately permissive: it accepts profiles produced by
    TrustInspect, hand-written YAML, and simple dicts from other tools.
    """
    raw_profile = raw_profile or {}
    if "target_profile" in raw_profile and isinstance(raw_profile["target_profile"], dict):
        raw_profile = raw_profile["target_profile"]

    identity = raw_profile.get("declared_identity") or raw_profile.get("identity") or raw_profile.get("role") or ""
    raw_response = raw_profile.get("profiling_response") or raw_profile.get("raw_profile_response") or ""
    text = " ".join([
        str(identity),
        str(raw_response),
        " ".join(_as_list(raw_profile.get("declared_capabilities"))),
        " ".join(_as_list(raw_profile.get("declared_boundaries"))),
    ])

    inferred_domain = raw_profile.get("domain_hint") or raw_profile.get("inferred_domain") or raw_profile.get("domain") or infer_domain_from_text(text)
    interaction_style = raw_profile.get("interaction_style") or infer_interaction_style(text)
    domain_entry = get_domain_entry(inferred_domain)

    declared_capabilities = _unique(_as_list(raw_profile.get("declared_capabilities")) + domain_entry.possible_actions)
    declared_boundaries = _unique(_as_list(raw_profile.get("declared_boundaries")) + [
        "should not disclose personal, sensitive, or confidential information",
        f"should stay within {domain_entry.domain} related assistance",
    ])

    sensitive_assets = _unique(
        _as_list(raw_profile.get("likely_sensitive_assets"))
        + _as_list(raw_profile.get("sensitive_assets"))
        + _as_list(raw_profile.get("forbidden_assets"))
        + domain_entry.sensitive_assets
    )
    possible_actions = _unique(_as_list(raw_profile.get("possible_actions")) + domain_entry.possible_actions)
    forbidden_actions = _unique(_as_list(raw_profile.get("forbidden_actions")) + domain_entry.forbidden_actions)

    risk_areas = _unique(_as_list(raw_profile.get("risk_areas")) + DEFAULT_RISK_AREAS)

    if possible_actions or forbidden_actions or interaction_style == "agentic_workflow":
        risk_areas = _unique(risk_areas + ACTION_RISKS)

    if "document" in text.lower() or "context" in text.lower() or "summarize" in text.lower():
        risk_areas = _unique(risk_areas + RAG_RISKS)

    return {
        **raw_profile,
        "declared_identity": identity or f"{domain_entry.domain.title()} assistant",
        "inferred_domain": domain_entry.domain,
        "interaction_style": interaction_style,
        "declared_capabilities": declared_capabilities,
        "declared_boundaries": declared_boundaries,
        "likely_sensitive_assets": sensitive_assets,
        "possible_actions": possible_actions,
        "forbidden_actions": forbidden_actions,
        "risk_areas": risk_areas,
        "note_subject": raw_profile.get("note_subject") or domain_entry.note_subject,
        "benign_context": raw_profile.get("benign_context") or domain_entry.benign_context,
        "benign_tail": raw_profile.get("benign_tail") or domain_entry.benign_tail,
    }
