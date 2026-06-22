from __future__ import annotations

from pathlib import Path
from typing import Dict

SUITES: Dict[str, str] = {
    # TrustInspect-native baseline catalog
    "trustinspect-baseline": "examples/test_cases/trustinspect_baseline.yaml",

    # OWASP Top 10 LLM 2025 static catalogs
    "owasp-llm-top10-2025-light": "examples/test_suites/owasp_llm_top10_2025_light.yaml",
    "owasp-llm-top10-2025-full": "examples/test_suites/owasp_llm_top10_2025_full.yaml",

    # Future catalog placeholder: do not map until implemented.
    # "owasp-aitg-32": "examples/test_suites/owasp_aitg_32.yaml",
}


def available_suites() -> list[str]:
    return sorted(SUITES.keys())


def resolve_suite_path(suite_id: str, project_root: str | Path | None = None) -> Path:
    if suite_id not in SUITES:
        known = ", ".join(available_suites())
        raise ValueError(f"Unknown TrustInspect suite '{suite_id}'. Available suites: {known}")

    root = Path(project_root or ".").resolve()
    path = root / SUITES[suite_id]
    if not path.exists():
        raise FileNotFoundError(f"Suite '{suite_id}' points to missing file: {path}")
    return path

# --- TrustInspect OWASP AITG suites ---
SUITES.setdefault('owasp-aitg-light', 'suites/owasp/aitg-light.yaml')
SUITES.setdefault('owasp-aitg-full', 'suites/owasp/aitg-full.yaml')
# --- End TrustInspect OWASP AITG suites ---
