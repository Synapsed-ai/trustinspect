from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable

SUITE_DISPLAY_NAMES = {
    "trustinspect-baseline": "TrustInspect Baseline",
    "owasp-llm-top10-2025-light": "OWASP LLM Top 10 2025 — Light",
    "owasp-llm-top10-2025-full": "OWASP LLM Top 10 2025 — Full",
    "owasp-aitg-light": "OWASP AI Testing Guide — Light",
    "owasp-aitg-full": "OWASP AI Testing Guide — Full",
}

SUITE_VERSIONS = {
    "trustinspect-baseline": "v0.3-alpha",
    "owasp-llm-top10-2025-light": "2025-light",
    "owasp-llm-top10-2025-full": "2025-full",
    "owasp-aitg-light": "v0.1-light",
    "owasp-aitg-full": "v0.1-full",
}


def _obj_to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if is_dataclass(value):
        try:
            return asdict(value)
        except Exception:
            pass
    result: dict[str, Any] = {}
    for key in ("id", "name", "category", "metadata", "mappings"):
        if hasattr(value, key):
            result[key] = getattr(value, key)
    return result


def _iter_observations(assessment: Any) -> Iterable[Any]:
    return getattr(assessment, "observations", []) or []


def _test_case_from_observation(observation: Any) -> dict[str, Any]:
    """Return a best-effort test case dict from different Observation shapes.

    TrustInspect evolved through several prototypes; some observations carry a
    full `test_case`, while others expose `test_id` / `test_case_id` directly.
    Suite inference must be resilient because it drives report metadata.
    """
    if isinstance(observation, dict):
        tc = observation.get("test_case") or observation.get("test") or observation
        result = _obj_to_dict(tc)
        for key in ("test_id", "test_case_id", "id"):
            if key in observation and "id" not in result:
                result["id"] = observation[key]
        return result

    tc = getattr(observation, "test_case", None)
    result = _obj_to_dict(tc)
    if not result:
        result = {}
    for attr in ("test_id", "test_case_id", "id"):
        value = getattr(observation, attr, None)
        if value and "id" not in result:
            result["id"] = value
    return result


def _collect_test_ids(assessment: Any) -> list[str]:
    ids: list[str] = []
    for obs in _iter_observations(assessment):
        tc = _test_case_from_observation(obs)
        test_id = tc.get("id") or tc.get("test_id")
        if test_id:
            ids.append(str(test_id))
    return ids


def _collect_metadata(assessment: Any) -> dict[str, Any]:
    md = getattr(assessment, "metadata", None)
    if isinstance(md, dict):
        return dict(md)
    return {}


def _infer_from_paths(metadata: dict[str, Any]) -> str | None:
    text = " ".join(str(v) for v in metadata.values() if isinstance(v, (str, Path))).lower()
    if "aitg-full" in text or "owasp_aitg_full" in text or "aitg_full" in text:
        return "owasp-aitg-full"
    if "aitg-light" in text or "owasp_aitg_light" in text or "aitg_light" in text:
        return "owasp-aitg-light"
    if "llm-top10-2025-full" in text or "owasp_llm_top10_2025_full" in text:
        return "owasp-llm-top10-2025-full"
    if "llm-top10-2025-light" in text or "owasp_llm_top10_2025_light" in text:
        return "owasp-llm-top10-2025-light"
    if "trustinspect_baseline" in text or "trustinspect-baseline" in text:
        return "trustinspect-baseline"
    return None


def _infer_from_ids(test_ids: list[str]) -> str | None:
    if not test_ids:
        return None
    upper_ids = [tid.upper() for tid in test_ids]
    total = len(upper_ids)
    if any(tid.startswith("AITG-") for tid in upper_ids):
        return "owasp-aitg-full" if total >= 100 else "owasp-aitg-light"
    if any(tid.startswith("OWASP-LLM") or tid.startswith("LLM") for tid in upper_ids):
        return "owasp-llm-top10-2025-full" if total > 50 else "owasp-llm-top10-2025-light"
    if any(tid.startswith("TI-BASE") or tid.startswith("TRUSTINSPECT") for tid in upper_ids):
        return "trustinspect-baseline"
    return None


def normalize_suite_id(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if not text or text == "-":
        return None
    lowered = text.lower().replace("_", "-")
    aliases = {
        "owasp-aitg-32": "owasp-aitg-light",
        "owasp-ai-testing-guide-light": "owasp-aitg-light",
        "owasp-ai-testing-guide-full": "owasp-aitg-full",
        "owasp-llm-top10-light": "owasp-llm-top10-2025-light",
        "owasp-llm-top10-full": "owasp-llm-top10-2025-full",
    }
    return aliases.get(lowered, lowered)


def enrich_assessment_suite_metadata(assessment: Any) -> Any:
    metadata = _collect_metadata(assessment)
    explicit_suite = (
        metadata.get("suite_id")
        or metadata.get("suite")
        or metadata.get("static_suite")
        or metadata.get("static_suite_id")
        or metadata.get("suite_name")
    )
    suite_id = normalize_suite_id(explicit_suite)
    if not suite_id:
        suite_id = _infer_from_paths(metadata)
    if not suite_id:
        suite_id = _infer_from_ids(_collect_test_ids(assessment))
    if suite_id:
        metadata["suite_id"] = suite_id
        metadata.setdefault("suite", suite_id)
        metadata["suite_display_name"] = SUITE_DISPLAY_NAMES.get(suite_id, str(explicit_suite or suite_id))
        metadata["suite_version"] = metadata.get("suite_version") or SUITE_VERSIONS.get(suite_id, "-")
    else:
        metadata.setdefault("suite_display_name", "-")
        metadata.setdefault("suite_version", "-")
    try:
        assessment.metadata = metadata
    except Exception:
        pass
    return assessment


def suite_display_name(assessment: Any) -> str:
    metadata = _collect_metadata(enrich_assessment_suite_metadata(assessment))
    return str(metadata.get("suite_display_name") or metadata.get("suite_id") or "-")
