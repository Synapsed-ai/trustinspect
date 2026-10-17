from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml


from trustinspect.core.indicator_types import SUPPORTED_MATCH_TYPES, normalize_indicator_fields


@dataclass
class ValidationIssue:
    level: str  # ERROR | WARNING
    location: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.location}: {self.message}"


@dataclass
class ValidationResult:
    path: Path
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.level == "ERROR" for issue in self.issues)

    def add(self, level: str, location: str, message: str) -> None:
        self.issues.append(ValidationIssue(level=level, location=location, message=message))


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_test_cases(data: Any) -> List[Dict[str, Any]]:
    """Read supported envelopes without discarding malformed rows."""
    if data is None:
        return []
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        envelopes = [key for key in ("test_cases", "tests") if key in data]
        if len(envelopes) > 1:
            raise ValueError("Use either 'test_cases' or 'tests', not both.")
        if envelopes:
            rows = data[envelopes[0]]
        elif any(key in data for key in ("id", "test_id", "prompt", "payload")):
            rows = [data]
        else:
            raise ValueError("Expected a test_cases/tests list or a single test case.")
    else:
        raise ValueError("Test catalog must be a list or mapping.")
    if not isinstance(rows, list):
        raise ValueError("test_cases/tests must be a list of mappings.")
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"test[{index}] must be a mapping.")
    return rows


def catalog_id(tc: Dict[str, Any]) -> str:
    return str(tc.get("id") or tc.get("test_id") or "<missing-id>")


def catalog_prompt(tc: Dict[str, Any]) -> str:
    return str(tc.get("payload") or tc.get("prompt") or "")


# Compatibility names; all readers use the same envelope and aliases.
_extract_test_cases = extract_test_cases
_get_id = catalog_id
_get_prompt = catalog_prompt


def _normalize_indicator(indicator: Any) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    normalized = normalize_indicator_fields(indicator)
    return normalized["value"], normalized["match"], normalized


def validate_test_catalog(path: str | Path) -> ValidationResult:
    path = Path(path)
    try:
        data = _load_yaml(path)
    except Exception as exc:
        result = ValidationResult(path=path)
        result.add("ERROR", str(path), f"YAML could not be parsed: {exc}")
        return result
    return validate_catalog_data(data, path)


def validate_catalog_data(data: Any, path: str | Path) -> ValidationResult:
    """Validate parsed input once, before a caller contacts the target."""
    path = Path(path)
    result = ValidationResult(path=path)
    try:
        test_cases = extract_test_cases(data)
    except ValueError as exc:
        result.add("ERROR", str(path), str(exc))
        return result
    if not test_cases:
        result.add("ERROR", str(path), "No test cases found. Expected 'test_cases:' list, 'tests:' list, or a single test case.")
        return result

    seen_ids: set[str] = set()

    for idx, tc in enumerate(test_cases, start=1):
        loc = f"{path}::test[{idx}]"
        test_id = _get_id(tc)

        if test_id == "<missing-id>":
            result.add("ERROR", loc, "Missing required id/test_id.")
        elif test_id in seen_ids:
            result.add("ERROR", loc, f"Duplicate test id: {test_id}")
        else:
            seen_ids.add(test_id)

        if not tc.get("name"):
            result.add("WARNING", f"{loc}:{test_id}", "Missing name.")

        if not tc.get("category"):
            result.add("WARNING", f"{loc}:{test_id}", "Missing category.")

        for key in ("payload", "prompt"):
            if key in tc and not isinstance(tc[key], str):
                result.add("ERROR", f"{loc}:{test_id}", f"{key} must be a string.")
        if tc.get("payload") and tc.get("prompt") and tc["payload"] != tc["prompt"]:
            result.add("ERROR", f"{loc}:{test_id}", "Conflicting payload and prompt aliases.")
        if tc.get("id") and tc.get("test_id") and str(tc["id"]) != str(tc["test_id"]):
            result.add("ERROR", loc, "Conflicting id and test_id aliases.")
        for key in ("metadata", "mappings"):
            if tc.get(key) is not None and not isinstance(tc[key], dict):
                result.add("ERROR", f"{loc}:{test_id}", f"{key} must be a mapping.")

        prompt = _get_prompt(tc)
        if not prompt.strip():
            result.add("ERROR", f"{loc}:{test_id}", "Prompt/payload is empty. The scanner would send an empty message.")

        if "<script" in prompt.lower():
            result.add("WARNING", f"{loc}:{test_id}", "Prompt contains HTML/JS. Report output must be escaped and treated as untrusted evidence.")

        if not tc.get("expected_behavior"):
            result.add("WARNING", f"{loc}:{test_id}", "Missing expected_behavior. Evidence analysis will be less explainable.")

        failure_indicators = tc.get("failure_indicators")
        if failure_indicators is None:
            failure_indicators = []
        if not isinstance(failure_indicators, list):
            result.add("ERROR", f"{loc}:{test_id}", "failure_indicators must be a list.")
            failure_indicators = []

        if not failure_indicators:
            result.add("WARNING", f"{loc}:{test_id}", "No failure_indicators defined. Classification may be weak or default to POSSIBLE/SAFE.")

        for j, indicator in enumerate(failure_indicators, start=1):
            iloc = f"{loc}:{test_id}:failure_indicators[{j}]"
            try:
                value, match, raw = _normalize_indicator(indicator)
            except ValueError as exc:
                result.add("ERROR", iloc, str(exc))
                continue

            if value and value.upper().endswith("SENTINEL") and match == "contains":
                result.add(
                    "WARNING",
                    iloc,
                    "Sentinel indicator uses broad 'contains'. Prefer 'ends_with_unquoted' to avoid mention-vs-execution false positives.",
                )

        meta = tc.get("metadata") if isinstance(tc.get("metadata"), dict) else {}
        source = tc.get("source") or meta.get("source")
        if source and (not isinstance(source, str) or source not in {"static", "baseline", "dynamic", "adaptive"}):
            result.add("WARNING", f"{loc}:{test_id}", f"Unusual source value: {source}")

    return result


def validate_many(paths: Iterable[str | Path]) -> List[ValidationResult]:
    return [validate_test_catalog(p) for p in paths]


def _print_results(results: List[ValidationResult]) -> int:
    total_errors = 0
    total_warnings = 0
    for result in results:
        print(f"\n== {result.path} ==")
        if not result.issues:
            print("OK: no issues found")
            continue
        for issue in result.issues:
            print(str(issue))
            if issue.level == "ERROR":
                total_errors += 1
            elif issue.level == "WARNING":
                total_warnings += 1
    print(f"\nValidation summary: {total_errors} error(s), {total_warnings} warning(s)")
    return 1 if total_errors else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TrustInspect test catalogs before scan execution.")
    parser.add_argument("paths", nargs="+", help="YAML test catalog files to validate")
    args = parser.parse_args(argv)
    return _print_results(validate_many(args.paths))


if __name__ == "__main__":
    raise SystemExit(main())
