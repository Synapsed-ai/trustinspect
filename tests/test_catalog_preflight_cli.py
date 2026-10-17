"""Use the public CLI; no browser/profiling action may precede a bad catalog."""
import sys

import pytest
import yaml

pytest.importorskip("selenium", reason="CLI imports the real Selenium dependency")
pytest.importorskip("webdriver_manager", reason="CLI imports its driver dependency")

from trustinspect import cli
from trustinspect.testcases.loader import load_test_cases_yaml


@pytest.mark.parametrize("command,flag", [("scan-web", "--test-cases"), ("adaptive-scan", "--base-test-cases")])
@pytest.mark.parametrize("indicators", ["SCHEMA_MARKER", False, 0, {"value": "x"}, [None]])
def test_invalid_catalog_stops_before_selectors_profiling_or_scanning(command, flag, indicators, tmp_path, monkeypatch):
    path = tmp_path / "invalid.yaml"
    path.write_text(yaml.safe_dump({"test_cases": [{"id": "CLI-01", "payload": "Request",
                                                    "failure_indicators": indicators}]}), encoding="utf-8")
    def unexpected(*args, **kwargs):
        pytest.fail("A browser/target operation ran before catalog validation")
    monkeypatch.setattr(cli, "_resolve_selectors", unexpected)
    monkeypatch.setattr(cli, "profile_target_via_web_ui", unexpected)
    monkeypatch.setattr(cli, "_run_web_assessment", unexpected)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["trustinspect", command, flag, str(path),
                                      "--target-url", "http://127.0.0.1:9", "--auto-selectors"])
    with pytest.raises(ValueError, match="failure_indicators"):
        cli.main()
    assert not (tmp_path / "reports").exists()


@pytest.mark.parametrize("envelope", ["single", "test_cases", "tests", "list"])
def test_cli_and_library_load_identical_cases(envelope, tmp_path):
    row = {"test_id": "SAME-01", "prompt": "Provide a response", "expected_behavior": "Keep boundaries",
           "failure_indicators": [{"value": "WHOLE_MARKER", "match": "contains", "evidence_role": "review"}]}
    data = row if envelope == "single" else [row] if envelope == "list" else {envelope: [row]}
    path = tmp_path / "case.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    assert cli._load_test_cases(path) == load_test_cases_yaml(path)
