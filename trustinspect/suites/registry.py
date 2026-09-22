from __future__ import annotations

from pathlib import Path
from typing import Dict

from trustinspect.resources import builtin_file

SUITES: Dict[str, str] = {
    "trustinspect-baseline": "examples/test_cases/trustinspect_baseline.yaml",
    "owasp-llm-top10-2025-light": "examples/test_suites/owasp_llm_top10_2025_light.yaml",
    "owasp-llm-top10-2025-full": "examples/test_suites/owasp_llm_top10_2025_full.yaml",
    "owasp-aitg-light": "suites/owasp/aitg-light.yaml",
    "owasp-aitg-full": "suites/owasp/aitg-full.yaml",
}


def available_suites() -> list[str]:
    return sorted(SUITES)


def resolve_suite_path(suite_id: str, project_root: str | Path | None = None) -> Path:
    if suite_id not in SUITES:
        raise ValueError(f"Unknown TrustInspect suite {suite_id!r}. Available suites: {', '.join(available_suites())}")
    if project_root is None:
        return builtin_file(SUITES[suite_id])
    # Explicit roots are honored; missing overrides must not silently fall back.
    path = Path(project_root).expanduser().resolve() / SUITES[suite_id]
    if not path.is_file():
        raise FileNotFoundError(f"Suite {suite_id!r} points to missing file: {path}")
    return path
