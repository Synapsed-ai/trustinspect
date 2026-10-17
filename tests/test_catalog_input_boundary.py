"""Exercise raw YAML through validation, loading, serialization and analysis."""
from dataclasses import replace

import pytest
import yaml

from trustinspect.analyzers.heuristic import HeuristicTrustAnalyzer
from trustinspect.core.models import Classification
from trustinspect.testcases.loader import load_test_case_rows, load_test_cases_yaml, save_test_cases_yaml
from trustinspect.testcases.validator import validate_test_catalog


def catalog(tmp_path, indicator, envelope="test_cases"):
    row = {"id": "BOUNDARY-01", "payload": "Provide a bounded answer.",
           "failure_indicators": indicator}
    data = row if envelope == "single" else [row] if envelope == "list" else {envelope: [row]}
    path = tmp_path / "case.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


INVALID = ["SCHEMA_MARKER", "", {"value": "SCHEMA_MARKER", "match": "contains"},
           {}, False, True, 0, 1, 0.0, [None], [42], [{"value": "x", "match": "typo"}],
           [{"value": "x", "case_sensitive": "false"}], [{"value": "[", "match": "regex"}]]


@pytest.mark.parametrize("value", INVALID)
@pytest.mark.parametrize("envelope", ["test_cases", "tests", "single", "list"])
def test_invalid_container_or_entry_rejected_before_coercion(value, envelope, tmp_path):
    path = catalog(tmp_path, value, envelope)
    assert not validate_test_catalog(path).ok
    for loader in (load_test_case_rows, load_test_cases_yaml):
        with pytest.raises(ValueError, match="failure_indicators"):
            loader(path)


@pytest.mark.parametrize("envelope", ["test_cases", "tests", "single", "list"])
@pytest.mark.parametrize("indicator", [["SCHEMA_MARKER"], [{"value": "SCHEMA_MARKER", "match": "contains"}]])
def test_supported_envelopes_keep_the_whole_indicator(envelope, indicator, tmp_path):
    path = catalog(tmp_path, indicator, envelope)
    assert validate_test_catalog(path).ok
    tc, = load_test_cases_yaml(path)
    assert tc.failure_indicators == indicator
    analyzer = HeuristicTrustAnalyzer()
    assert analyzer.analyze(tc, "I cannot disclose protected data.")[0] == Classification.SAFE
    assert analyzer.analyze(tc, "The token is SCHEMA_MARKER.")[0] == Classification.VULNERABILITY


@pytest.mark.parametrize("value", [None, []])
def test_optional_empty_indicators_are_explicit_not_false_scalars(value, tmp_path):
    path = catalog(tmp_path, value)
    assert validate_test_catalog(path).ok
    assert load_test_cases_yaml(path)[0].failure_indicators == []


@pytest.mark.parametrize("data", [None, [], {}, {"test_cases": []}, {"tests": [1]},
                                   {"test_cases": [{"id": "OK", "payload": "x"}, False]},
                                   {"test_cases": [], "tests": []}])
def test_bad_or_empty_envelopes_never_silently_drop_cases(data, tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    assert not validate_test_catalog(path).ok
    with pytest.raises(ValueError):
        load_test_cases_yaml(path)


def test_aliases_and_metadata_survive_round_trip(tmp_path):
    path = tmp_path / "aliases.yaml"
    path.write_text(yaml.safe_dump({"test_id": "ALIAS-01", "prompt": "Literal request",
        "expected_behavior": "Preserve the boundary", "metadata": {"custom": "retained"},
        "failure_indicators": [{"value": "x", "match": "contains", "evidence_role": "review"}]}), encoding="utf-8")
    tc, = load_test_cases_yaml(path)
    assert tc.id == "ALIAS-01" and tc.payload == "Literal request"
    assert tc.objective == "Preserve the boundary" and tc.metadata["custom"] == "retained"
    output = save_test_cases_yaml([tc], tmp_path / "saved.yaml")
    assert load_test_cases_yaml(output) == [tc]


@pytest.mark.parametrize("value", INVALID[:9])
def test_serializer_does_not_launder_invalid_types(value, tmp_path):
    good = load_test_cases_yaml(catalog(tmp_path, ["WHOLE_MARKER"]))[0]
    for candidate in (replace(good, failure_indicators=value),
                      {"id": "BAD", "payload": "Request", "failure_indicators": value}):
        output = tmp_path / "preserved.yaml"
        output.write_text("existing content", encoding="utf-8")
        with pytest.raises(ValueError):
            save_test_cases_yaml([candidate], output)
        assert output.read_text() == "existing content"


@pytest.mark.parametrize("changes", [{"payload": False}, {"prompt": "different"},
                                     {"test_id": "different"}, {"metadata": []}, {"mappings": "x"}])
def test_nonconforming_row_fields_fail_consistently(changes, tmp_path):
    path = tmp_path / "bad-row.yaml"
    path.write_text(yaml.safe_dump({"id": "ROW", "payload": "Request", **changes}), encoding="utf-8")
    assert not validate_test_catalog(path).ok
    with pytest.raises(ValueError):
        load_test_cases_yaml(path)


def test_duplicate_ids_fail_loading_as_well_as_validation(tmp_path):
    path = tmp_path / "duplicate.yaml"
    path.write_text(yaml.safe_dump([{"id": "SAME", "payload": "Request"}] * 2))
    assert not validate_test_catalog(path).ok
    with pytest.raises(ValueError, match="Duplicate test id"):
        load_test_cases_yaml(path)


@pytest.mark.parametrize("value", INVALID[:9])
def test_direct_analyzer_rejects_bad_containers_before_capture_helpers(value, tmp_path):
    tc = load_test_cases_yaml(catalog(tmp_path, ["WHOLE_MARKER"]))[0]
    tc.failure_indicators = value
    assert HeuristicTrustAnalyzer().analyze(tc, "I cannot disclose protected data.")[0] == Classification.ERROR
