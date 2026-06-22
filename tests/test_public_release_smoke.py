from __future__ import annotations

from pathlib import Path
import importlib
import yaml


def test_public_imports_smoke():
    modules = [
        "trustinspect.cli",
        "trustinspect.core.models",
        "trustinspect.reporting.html_report",
        "trustinspect.analyzers.heuristic",
        "trustinspect.dynamic.engine",
        "trustinspect.targets.registry",
    ]
    for module in modules:
        importlib.import_module(module)


def test_public_suites_are_present_and_valid_yaml():
    suite_paths = [
        Path("suites/owasp/llm-top10-2025-light.yaml"),
        Path("suites/owasp/llm-top10-2025-full.yaml"),
        Path("suites/owasp/aitg-light.yaml"),
        Path("suites/owasp/aitg-full.yaml"),
    ]
    existing = [p for p in suite_paths if p.exists()]
    assert existing, "No public suite files found under suites/owasp/."

    for path in existing:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"{path} must be a YAML mapping."
        cases = data.get("test_cases") or data.get("tests") or []
        assert isinstance(cases, list), f"{path} test cases must be a list."
        assert len(cases) > 0, f"{path} must contain at least one test case."


def test_active_report_template_has_no_embedded_base64_image():
    candidates = [
        Path("trustinspect/reporting/templates/assessment_report.html.j2"),
        Path("trustinspect/reporting/templates/assessment_report.html"),
    ]
    existing = [p for p in candidates if p.exists()]
    assert existing, "No assessment report template found."
    for path in existing:
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert "data:image/png;base64" not in text, f"{path} still embeds base64 image assets."


def test_demo_chatbot_files_exist():
    demo = Path("demos/trustinspect-demo-chatbot")
    assert demo.exists(), "Local demo chatbot target is missing."
    assert (demo / "app" / "main.py").exists(), "Demo chatbot app/main.py is missing."
    assert (demo / "run_vulnerable.sh").exists(), "run_vulnerable.sh is missing."
    assert (demo / "run_hardened.sh").exists(), "run_hardened.sh is missing."
