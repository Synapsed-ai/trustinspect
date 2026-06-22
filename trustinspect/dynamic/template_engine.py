from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from .indicator_compiler import SafeFormatDict, compile_failure_indicators, compile_success_indicators
from .risk_mapper import normalize_target_profile


def load_dynamic_templates(template_dir: str | Path) -> List[Dict[str, Any]]:
    template_path = Path(template_dir)
    templates: List[Dict[str, Any]] = []
    for path in sorted(template_path.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if data:
            data.setdefault("template_id", path.stem)
            templates.append(data)
    return templates


def _join_list(values: List[str], fallback: str) -> str:
    values = [v for v in values if v]
    if not values:
        return fallback
    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + ", and " + values[-1]


def build_template_variables(profile: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    profile = normalize_target_profile(profile)
    assets = profile.get("likely_sensitive_assets") or ["sensitive information"]
    actions = profile.get("forbidden_actions") or profile.get("possible_actions") or ["perform an unauthorized action"]
    capabilities = profile.get("declared_capabilities") or ["answer user questions"]
    boundaries = profile.get("declared_boundaries") or ["follow safety and privacy boundaries"]

    variables: Dict[str, Any] = {
        "domain": profile.get("inferred_domain", "generic"),
        "interaction_style": profile.get("interaction_style", "assistant"),
        "declared_identity": profile.get("declared_identity", "assistant"),
        "asset_list": _join_list(assets, "sensitive information"),
        "primary_asset": assets[0] if assets else "sensitive information",
        "sensitive_asset_example": assets[0] if assets else "sensitive information",
        "action": actions[0] if actions else "perform an unauthorized action",
        "action_list": _join_list(actions, "perform an unauthorized action"),
        "capability_list": _join_list(capabilities, "answer user questions"),
        "boundary_list": _join_list(boundaries, "follow safety and privacy boundaries"),
        "note_subject": profile.get("note_subject", "support note"),
        "benign_context": profile.get("benign_context", "The user asked for help with a normal support request."),
        "benign_tail": profile.get("benign_tail", "The note discusses safe and reliable assistance."),
        "sentinel": template.get("sentinel", "TRUSTINSPECT_SENTINEL"),
        "action_sentinel": template.get("action_sentinel", "ACTION_CONFIRMED_TEST"),
        "unsafe_echo_payload": template.get("unsafe_echo_payload", "<script>alert('TRUSTINSPECT_XSS')</script>"),
    }

    for key, value in (template.get("variables") or {}).items():
        if isinstance(value, str):
            variables[key] = value.format_map(SafeFormatDict(variables))
        else:
            variables[key] = value
    return variables


def render_template(template: Dict[str, Any], profile: Dict[str, Any], index: int) -> Dict[str, Any]:
    profile = normalize_target_profile(profile)
    variables = build_template_variables(profile, template)
    risk_area = template.get("risk_area", "prompt_manipulation")

    prompt = (template.get("prompt_template") or "").format_map(SafeFormatDict(variables))
    expected_behavior = (template.get("expected_behavior") or "").format_map(SafeFormatDict(variables))
    generation_reason = (template.get("generation_reason_template") or template.get("generation_reason") or "Selected from target profile.").format_map(SafeFormatDict({**variables, "risk_area": risk_area}))

    test_id = template.get("id") or f"TI-DYN-{index:03d}"

    return {
        "id": test_id,
        "name": template.get("name", template.get("template_id", test_id)),
        "source": "dynamic",
        "category": template.get("category", "Trustworthy AI / Dynamic"),
        "trustworthiness_dimension": template.get("trustworthiness_dimension", "Trustworthiness"),
        "risk_area": risk_area,
        "prompt": prompt,
        "expected_behavior": expected_behavior,
        "failure_indicators": compile_failure_indicators(template.get("failure_indicators") or [], variables, risk_area),
        "success_indicators": compile_success_indicators(template.get("success_indicators") or [], variables),
        "severity": template.get("severity", "medium"),
        "metadata": {
            "source": "dynamic",
            "template_id": template.get("template_id", test_id),
            "template_priority": template.get("priority", 50),
            "risk_area": risk_area,
            "generation_reason": generation_reason,
            "target_domain": profile.get("inferred_domain"),
            "interaction_style": profile.get("interaction_style"),
        },
    }
