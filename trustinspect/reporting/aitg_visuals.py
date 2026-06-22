from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

AITG_LAYER_BY_PREFIX = {
    "AITG-APP": "AI Application Testing",
    "AITG-MOD": "AI Model Testing",
    "AITG-INF": "AI Infrastructure Testing",
    "AITG-DAT": "AI Data Testing",
}

AITG_LAYER_ORDER = [
    "AI Application Testing",
    "AI Model Testing",
    "AI Infrastructure Testing",
    "AI Data Testing",
]


_STATUS_ORDER = ("vulnerabilities", "possible", "errors", "safe")


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _upper(value: Any) -> str:
    return str(value or "").strip().upper()


def _test_id_from_observation(observation: Any) -> str:
    for attr in ("test_id", "test_case_id", "id"):
        value = _get(observation, attr)
        if value:
            return str(value)

    test_case = _get(observation, "test_case")
    if test_case is not None:
        for attr in ("id", "test_id", "test_case_id"):
            value = _get(test_case, attr)
            if value:
                return str(value)

    return ""


def aitg_layer_for_test_id(test_id: str) -> Optional[str]:
    value = str(test_id or "")
    for prefix, layer in AITG_LAYER_BY_PREFIX.items():
        if value.startswith(prefix):
            return layer
    return None


def _classification_bucket(observation: Any) -> str:
    value = _upper(_get(observation, "classification"))
    if not value:
        value = _upper(_get(observation, "status"))

    if "VULNERABILITY" in value and "POSSIBLE" not in value:
        return "vulnerabilities"
    if "POSSIBLE" in value:
        return "possible"
    if "ERROR" in value:
        return "errors"
    if "SAFE" in value:
        return "safe"
    return "other"


def build_aitg_visual_summary(assessment: Any) -> Dict[str, Any]:
    """Build lightweight OWASP AITG layer counts for report rendering.

    This function intentionally uses only the official OWASP AITG layers as
    report categories. It does not expose TrustInspect-specific dimensions such
    as Privacy, Robustness, or Human Oversight in the AITG visualization.
    """

    rows: Dict[str, Dict[str, Any]] = {
        layer: {
            "layer": layer,
            "total": 0,
            "vulnerabilities": 0,
            "possible": 0,
            "safe": 0,
            "errors": 0,
            "other": 0,
            "finding_ratio": 0,
            "effective": 0,
        }
        for layer in AITG_LAYER_ORDER
    }

    observations = _get(assessment, "observations", []) or []
    for observation in observations:
        test_id = _test_id_from_observation(observation)
        layer = aitg_layer_for_test_id(test_id)
        if not layer:
            continue

        row = rows[layer]
        row["total"] += 1
        bucket = _classification_bucket(observation)
        row[bucket] = row.get(bucket, 0) + 1
        if bucket != "errors":
            row["effective"] += 1

    for row in rows.values():
        total = row["total"] or 0
        findings = row["vulnerabilities"]
        row["finding_ratio"] = int(round((findings / total) * 100)) if total else 0
        row["safe_ratio"] = int(round((row["safe"] / total) * 100)) if total else 0
        row["error_ratio"] = int(round((row["errors"] / total) * 100)) if total else 0
        row["possible_ratio"] = int(round((row["possible"] / total) * 100)) if total else 0

    active_rows = [rows[layer] for layer in AITG_LAYER_ORDER if rows[layer]["total"] > 0]
    totals = {
        "total": sum(row["total"] for row in active_rows),
        "vulnerabilities": sum(row["vulnerabilities"] for row in active_rows),
        "possible": sum(row["possible"] for row in active_rows),
        "safe": sum(row["safe"] for row in active_rows),
        "errors": sum(row["errors"] for row in active_rows),
        "effective": sum(row["effective"] for row in active_rows),
    }

    return {
        "is_aitg": bool(active_rows),
        "layers": active_rows,
        "totals": totals,
        "layer_names": AITG_LAYER_ORDER,
    }


def enrich_assessment_for_aitg_visuals(assessment: Any) -> Any:
    """Attach OWASP AITG visual summary into assessment.metadata."""

    metadata = _get(assessment, "metadata", None)
    if metadata is None:
        try:
            assessment.metadata = {}
            metadata = assessment.metadata
        except Exception:
            return assessment

    if not isinstance(metadata, MutableMapping):
        return assessment

    metadata["aitg_visual_summary"] = build_aitg_visual_summary(assessment)
    return assessment
