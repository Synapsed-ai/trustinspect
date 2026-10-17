from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import yaml

from trustinspect.core.models import TestCase
from trustinspect.resources import resolve_input_file
from trustinspect.core.indicator_types import validated_indicator_list


def load_test_case_rows(path: str | Path) -> list[dict]:
    # Avoid preloading the standalone validator when invoked with python -m.
    from trustinspect.testcases.validator import (
        catalog_id, catalog_prompt, extract_test_cases, validate_catalog_data,
    )
    resolved = resolve_input_file(path)
    try:
        data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML test catalog: {resolved}") from exc
    validation = validate_catalog_data(data, resolved)
    errors = [str(issue) for issue in validation.issues if issue.level == "ERROR"]
    if errors:
        raise ValueError("Invalid test catalog:\n" + "\n".join(errors))
    rows = []
    for row in extract_test_cases(data):
        # Canonical aliases, while retaining every original author/metadata field.
        rows.append({**row, "id": catalog_id(row), "payload": catalog_prompt(row),
                     "failure_indicators": validated_indicator_list(row.get("failure_indicators"))})
    return rows


def load_test_cases_yaml(path: str | Path) -> List[TestCase]:
    rows = load_test_case_rows(path)
    cases: List[TestCase] = []
    for idx, row in enumerate(rows, 1):
        cases.append(
            TestCase(
                id=str(row.get("id") or f"TC-{idx:03d}"),
                name=str(row.get("name") or "TrustInspect Test Case"),
                category=str(row.get("category") or "Uncategorized"),
                objective=str(row.get("objective") or row.get("expected_behavior") or "Execute TrustInspect test case and observe target behavior."),
                payload=str(row.get("payload") or ""),
                expected_behavior=row.get("expected_behavior"),
                failure_indicators=validated_indicator_list(row.get("failure_indicators")),
                mappings=dict(row.get("mappings") or {}),
                metadata=dict(row.get("metadata") or {}),
            )
        )
    return cases


def test_case_to_dict(test_case: TestCase) -> dict:

    # TrustInspect dynamic engine may already return plain dictionaries.
    # The YAML serializer must accept both TestCase objects and dict-based
    # generated test cases. Keep prompt/payload aliases for backward compatibility.
    if isinstance(test_case, dict):
        data = dict(test_case)
        if "payload" not in data and "prompt" in data:
            data["payload"] = data["prompt"]
        if "prompt" not in data and "payload" in data:
            data["prompt"] = data["payload"]
        data["failure_indicators"] = validated_indicator_list(data.get("failure_indicators"))
        data.setdefault("metadata", {})
        return data
    return {
        "id": test_case.id,
        "name": test_case.name,
        "category": test_case.category,
        "objective": test_case.objective,
        "payload": test_case.payload,
        "expected_behavior": test_case.expected_behavior,
        "failure_indicators": validated_indicator_list(test_case.failure_indicators),
        "mappings": dict(test_case.mappings or {}),
        "metadata": dict(test_case.metadata or {}),
    }


def save_test_cases_yaml(test_cases: Iterable[TestCase], path: str | Path, metadata: dict | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"metadata": metadata or {}, "test_cases": [test_case_to_dict(tc) for tc in test_cases]}
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path
