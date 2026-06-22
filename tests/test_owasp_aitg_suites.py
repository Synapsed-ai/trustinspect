from pathlib import Path
import yaml

LIGHT = Path("suites/owasp/aitg-light.yaml")
FULL = Path("suites/owasp/aitg-full.yaml")

OFFICIAL_DATA_IDS = {
    "AITG-DAT-01": "Testing for Training Data Exposure",
    "AITG-DAT-02": "Testing for Runtime Exfiltration",
    "AITG-DAT-03": "Testing for Dataset Diversity & Coverage",
    "AITG-DAT-04": "Testing for Harmful Content in Data",
    "AITG-DAT-05": "Testing for Data Minimization & Consent",
}


def _load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_aitg_light_has_32_tests_and_no_execution_mode():
    data = _load(LIGHT)
    cases = data["test_cases"]
    assert len(cases) == 32
    assert all("execution_mode" not in c for c in cases)
    assert {c["id"] for c in cases if c["id"].startswith("AITG-DAT-")} == set(OFFICIAL_DATA_IDS)


def test_aitg_full_has_160_tests_and_no_execution_mode():
    data = _load(FULL)
    cases = data["test_cases"]
    assert len(cases) == 160
    assert all("execution_mode" not in c for c in cases)
    assert len([c for c in cases if c["parent_aitg_id"].startswith("AITG-DAT-")]) == 25


def test_aitg_data_titles_are_aligned_to_official_data_category():
    cases = _load(LIGHT)["test_cases"]
    by_id = {c["id"]: c for c in cases}
    for tid, title in OFFICIAL_DATA_IDS.items():
        assert by_id[tid]["name"] == title
        assert by_id[tid]["aitg_layer"] == "AI Data Testing"
        assert by_id[tid].get("prompt")
        assert by_id[tid].get("evidence_objective")


def test_aitg_test_case_contract_minimum_fields():
    cases = _load(LIGHT)["test_cases"]
    required = {"id", "name", "aitg_layer", "category", "risk_area", "prompt", "expected_behavior", "failure_indicators", "evidence_objective"}
    for case in cases:
        assert required.issubset(case.keys()), case["id"]
        assert case["prompt"] == case["payload"]
