from __future__ import annotations

from typing import Any, Dict, List


def template_applies(template: Dict[str, Any], profile: Dict[str, Any]) -> bool:
    applies_to = template.get("applies_to") or {}
    if not applies_to:
        return True

    profile_domain = profile.get("inferred_domain") or "generic"
    profile_style = profile.get("interaction_style") or "assistant"
    profile_risks = set(profile.get("risk_areas") or [])

    domains = applies_to.get("domains") or []
    styles = applies_to.get("interaction_styles") or []
    risks = applies_to.get("risk_areas") or []

    if domains and "any" not in domains and profile_domain not in domains:
        return False
    if styles and "any" not in styles and profile_style not in styles:
        return False
    if risks and not profile_risks.intersection(set(risks)):
        return False

    return True


def plan_templates(templates: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    applicable = [t for t in templates if template_applies(t, profile)]
    return sorted(applicable, key=lambda t: int(t.get("priority", 50)))
