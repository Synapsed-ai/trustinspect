from __future__ import annotations

from typing import Any, Dict, Iterable, List


DEFAULT_MATCH_BY_RISK = {
    "hidden_instruction_following": "ends_with_unquoted",
    "unauthorized_action_request": "claims_completion",
    "excessive_agency": "claims_completion",
    "sensitive_data_exposure": "disclosure_claim",
    "system_instruction_disclosure": "disclosure_claim",
    "unsafe_output_echo": "unsafe_echo",
    "resource_exhaustion": "output_length_over",
}


class SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def render_value(value: Any, variables: Dict[str, Any]) -> Any:
    if isinstance(value, str):
        return value.format_map(SafeFormatDict(variables))
    return value


def compile_failure_indicators(
    indicators: Iterable[Any],
    variables: Dict[str, Any],
    risk_area: str,
) -> List[Dict[str, Any]]:
    compiled: List[Dict[str, Any]] = []
    default_match = DEFAULT_MATCH_BY_RISK.get(risk_area, "contains_unquoted")

    for item in indicators or []:
        if isinstance(item, str):
            compiled.append({
                "value": render_value(item, variables),
                "match": default_match,
                "quoted_mentions_allowed": False,
            })
            continue

        if isinstance(item, dict):
            normalized = dict(item)
            if "value" in normalized:
                normalized["value"] = render_value(normalized["value"], variables)
            if "threshold" in normalized:
                normalized["threshold"] = normalized["threshold"]
            normalized.setdefault("match", default_match)
            normalized.setdefault("quoted_mentions_allowed", False)
            compiled.append(normalized)
            continue

        compiled.append({
            "value": str(item),
            "match": default_match,
            "quoted_mentions_allowed": False,
        })

    return compiled


def compile_success_indicators(indicators: Iterable[Any], variables: Dict[str, Any]) -> List[str]:
    result: List[str] = []
    for item in indicators or []:
        result.append(str(render_value(item, variables)))
    return result
