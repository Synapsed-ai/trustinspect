from __future__ import annotations

from typing import Any, Dict, List, Optional


RISK_PRIORITY = [
    "hidden_instruction_following",
    "sensitive_data_exposure",
    "system_instruction_disclosure",
    "unauthorized_action_request",
    "domain_boundary_escape",
    "unsafe_output_echo",
    "prompt_manipulation",
    "resource_exhaustion",
    "excessive_agency",
    "context_manipulation",
]


def _priority_key(test_case: Dict[str, Any]) -> tuple:
    risk = test_case.get("risk_area") or test_case.get("metadata", {}).get("risk_area") or ""
    try:
        risk_index = RISK_PRIORITY.index(risk)
    except ValueError:
        risk_index = len(RISK_PRIORITY)
    template_priority = int(test_case.get("metadata", {}).get("template_priority", 50))
    return (risk_index, template_priority, test_case.get("id", ""))


def select_dynamic_tests(candidates: List[Dict[str, Any]], max_dynamic_tests: Optional[int] = None) -> List[Dict[str, Any]]:
    """Limit dynamic tests only. Static/baseline tests must not be passed here."""
    ordered = sorted(candidates, key=_priority_key)
    if max_dynamic_tests is None or max_dynamic_tests <= 0:
        return ordered
    return ordered[:max_dynamic_tests]
