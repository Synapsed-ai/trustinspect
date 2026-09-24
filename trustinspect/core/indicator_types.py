"""One schema for catalog validation and runtime failure predicates."""
from __future__ import annotations

import re
from typing import Any

SUPPORTED_MATCH_TYPES = frozenset({
    "contains", "contains_anywhere", "contains_unquoted", "ends_with",
    "ends_with_unquoted", "exact", "exact_match", "regex",
    "disclosure_claim", "specific_internal_claim", "claims_access",
    "claims_completion", "unsafe_echo", "output_length_over",
})

# Claims and raw output alone do not establish downstream effects or provenance.
REVIEW_ONLY_MATCH_TYPES = frozenset({
    "disclosure_claim", "specific_internal_claim", "claims_access",
    "claims_completion", "unsafe_echo",
})


def normalize_indicator_fields(indicator: Any) -> dict[str, Any]:
    """Validate a legacy string or structured predicate before evaluation.

    Historical value/match aliases remain supported. Malformed YAML scalars,
    whitespace-only values, and string booleans are rejected rather than being
    coerced into a predicate with different semantics.
    """
    if isinstance(indicator, str):
        raw: dict[str, Any] = {"value": indicator}
    elif isinstance(indicator, dict):
        raw = indicator
    else:
        raise ValueError("Failure indicator must be a string or mapping.")

    value = raw.get("value") or raw.get("pattern") or raw.get("indicator")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Failure indicator requires a non-empty string value.")
    match = "contains"
    for name in ("match", "match_type", "type"):
        option = raw.get(name)
        if option is None or option == "":
            continue
        if not isinstance(option, str):
            raise ValueError("Failure indicator match type must be a string.")
        match = option.strip().lower()
        break
    if match not in SUPPORTED_MATCH_TYPES:
        raise ValueError(f"Unsupported failure indicator match type: {match}.")

    normalized: dict[str, Any] = {"value": value.strip(), "match": match}
    for name, default in (("quoted_mentions_allowed", True),
                          ("negative_context_enabled", True),
                          ("case_sensitive", False)):
        option = raw.get(name, default)
        if type(option) is not bool:
            raise ValueError(f"{name} must be a boolean, not a string or number.")
        normalized[name] = option
    normalized["threshold"] = raw.get("threshold")
    if match == "output_length_over":
        threshold = normalized["threshold"]
        if type(threshold) is not int or threshold <= 0:
            raise ValueError("output_length_over requires a positive integer threshold.")
    if match == "regex":
        flags = 0 if normalized["case_sensitive"] else re.IGNORECASE | re.DOTALL
        try:
            re.compile(normalized["value"], flags)
        except re.error as exc:
            raise ValueError("Invalid failure indicator regular expression.") from exc
    return normalized
