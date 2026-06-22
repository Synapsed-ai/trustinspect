from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


REQUIRED_TEMPLATE_FIELDS = {
    "template_id",
    "name",
    "risk_area",
    "category",
    "prompt_template",
    "expected_behavior",
    "failure_indicators",
    "generation_reason_template",
}

PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def validate_template(path: str | Path) -> List[str]:
    path = Path(path)
    issues: List[str] = []
    try:
        data = _load_yaml(path)
    except Exception as exc:
        return [f"ERROR {path}: YAML could not be parsed: {exc}"]

    if not isinstance(data, dict):
        return [f"ERROR {path}: template must be a YAML mapping/object"]

    for field in sorted(REQUIRED_TEMPLATE_FIELDS):
        if field not in data:
            issues.append(f"ERROR {path}: missing required field '{field}'")

    prompt_template = str(data.get("prompt_template") or "")
    if not prompt_template.strip():
        issues.append(f"ERROR {path}: prompt_template is empty")

    if "<script" in prompt_template.lower():
        issues.append(f"WARNING {path}: prompt_template contains HTML/JS; reports must escape evidence")

    indicators = data.get("failure_indicators") or []
    if not isinstance(indicators, list):
        issues.append(f"ERROR {path}: failure_indicators must be a list")
    elif not indicators:
        issues.append(f"WARNING {path}: no failure_indicators defined")

    placeholders = set(PLACEHOLDER_RE.findall(prompt_template))
    reason_placeholders = set(PLACEHOLDER_RE.findall(str(data.get("generation_reason_template") or "")))
    all_placeholders = placeholders | reason_placeholders
    safe_builtins = {
        "domain",
        "domain_label",
        "sensitive_assets",
        "sensitive_asset_example",
        "unsafe_action",
        "benign_context",
        "benign_tail",
        "sentinel",
        "risk_area",
        "target_identity",
        "declared_identity",
        "interaction_style",
    }
    # We don't error on unknown placeholders because domain_taxonomy may provide them;
    # we warn so template authors can review.
    for placeholder in sorted(all_placeholders - safe_builtins):
        issues.append(f"WARNING {path}: placeholder '{{{placeholder}}}' is not in the known built-in placeholder set")

    for idx, indicator in enumerate(indicators, start=1):
        if isinstance(indicator, str):
            if indicator.upper().endswith("SENTINEL"):
                issues.append(
                    f"WARNING {path}: failure indicator #{idx} uses raw string sentinel; prefer structured ends_with_unquoted"
                )
            continue
        if not isinstance(indicator, dict):
            issues.append(f"ERROR {path}: failure indicator #{idx} must be string or mapping")
            continue
        if not indicator.get("value"):
            issues.append(f"ERROR {path}: failure indicator #{idx} missing value")
        if not indicator.get("match"):
            issues.append(f"ERROR {path}: failure indicator #{idx} missing match")

    return issues


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TrustInspect dynamic templates.")
    parser.add_argument("template_dir", help="Directory containing dynamic template YAML files")
    args = parser.parse_args(argv)

    paths = sorted(Path(args.template_dir).glob("*.yaml"))
    if not paths:
        print(f"ERROR: no YAML templates found in {args.template_dir}")
        return 1

    errors = 0
    warnings = 0
    for path in paths:
        issues = validate_template(path)
        if not issues:
            print(f"OK {path}")
            continue
        for issue in issues:
            print(issue)
            if issue.startswith("ERROR"):
                errors += 1
            elif issue.startswith("WARNING"):
                warnings += 1

    print(f"\nTemplate validation summary: {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
