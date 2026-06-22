from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .budget import select_dynamic_tests
from .planner import plan_templates
from .risk_mapper import normalize_target_profile
from .template_engine import load_dynamic_templates, render_template


def load_profile(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if "target_profile" in data and isinstance(data["target_profile"], dict):
        return data["target_profile"]
    return data


def write_tests_yaml(test_cases: List[Dict[str, Any]], output: str | Path) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"test_cases": test_cases}
    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)


class DynamicTestEngine:
    def __init__(self, template_dir: str | Path = "examples/dynamic_templates") -> None:
        self.template_dir = Path(template_dir)

    def generate(self, target_profile: Dict[str, Any], max_dynamic_tests: Optional[int] = None) -> List[Dict[str, Any]]:
        profile = normalize_target_profile(target_profile)
        templates = load_dynamic_templates(self.template_dir)
        planned = plan_templates(templates, profile)
        candidates = [render_template(template, profile, index=i) for i, template in enumerate(planned, start=1)]
        return select_dynamic_tests(candidates, max_dynamic_tests=max_dynamic_tests)


def generate_dynamic_tests(
    target_profile: Dict[str, Any],
    max_dynamic_tests: Optional[int] = None,
    template_dir: str | Path = "examples/dynamic_templates",
) -> List[Dict[str, Any]]:
    return DynamicTestEngine(template_dir=template_dir).generate(target_profile, max_dynamic_tests=max_dynamic_tests)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TrustInspect dynamic test cases from a target profile.")
    parser.add_argument("--target-profile", required=True)
    parser.add_argument("--template-dir", default="examples/dynamic_templates")
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-dynamic-tests", type=int, default=8)
    parser.add_argument("--max-tests", type=int, help="Alias for --max-dynamic-tests.")
    args = parser.parse_args()

    max_tests = args.max_tests if args.max_tests is not None else args.max_dynamic_tests
    profile = load_profile(args.target_profile)
    tests = generate_dynamic_tests(profile, max_dynamic_tests=max_tests, template_dir=args.template_dir)
    write_tests_yaml(tests, args.output)
    print(f"[+] Generated {len(tests)} dynamic test cases: {args.output}")


if __name__ == "__main__":
    main()
