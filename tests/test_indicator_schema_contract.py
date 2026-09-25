"""Catalog validation and analysis must accept and reject the same predicates."""
from __future__ import annotations

import pytest
import yaml

from trustinspect.analyzers.heuristic import HeuristicTrustAnalyzer
from trustinspect.core.indicator_types import normalize_indicator_fields
from trustinspect.core.models import Classification, TestCase as Case
from trustinspect.testcases.validator import validate_test_catalog


def make_case(indicator):
    return Case(id="SCHEMA-001", name="Schema contract", category="test",
                objective="Validate the predicate", payload="Provide a bounded answer.",
                failure_indicators=[indicator])


INVALID = [None, 42, 0, True, [], {}, "", "  ",
           {"value": "  "}, {"value": 42}, {"value": False},
           {"value": "SCHEMA_MARKER", "match": []},
           {"value": "SCHEMA_MARKER", "match": "unknown"},
           {"value": "[", "match": "regex"},
           {"value": "x", "match": "output_length_over", "threshold": True},
           {"value": "x", "match": "output_length_over", "threshold": "10"}]
INVALID.extend({"value": "SCHEMA_MARKER", "match": value}
               for value in (["contains"], 0, False, {}))
INVALID.extend({"value": "SCHEMA_MARKER", key: value}
               for key in ("case_sensitive", "quoted_mentions_allowed", "negative_context_enabled")
               for value in ("false", 0, None))


@pytest.mark.parametrize("indicator", INVALID)
def test_malformed_predicates_fail_both_layers(indicator, tmp_path):
    path = tmp_path / "schema.yaml"
    path.write_text(yaml.safe_dump({"test_cases": [{"id": "SCHEMA-001",
                    "payload": "Provide a bounded answer.", "failure_indicators": [indicator]}]}), encoding="utf-8")
    assert not validate_test_catalog(path).ok
    result = HeuristicTrustAnalyzer().analyze(make_case(indicator), "I cannot disclose protected data.")
    assert result[0] == Classification.ERROR, result


@pytest.mark.parametrize("value_key", ["value", "pattern", "indicator"])
@pytest.mark.parametrize("match_key", ["match", "match_type", "type"])
def test_legacy_field_aliases_normalize_consistently(value_key, match_key, tmp_path):
    indicator = {value_key: " SCHEMA_MARKER ", match_key: " EXACT_MATCH "}
    path = tmp_path / "schema.yaml"
    path.write_text(yaml.safe_dump({"test_cases": [{"id": "SCHEMA-001",
                    "payload": "Provide a bounded answer.", "failure_indicators": [indicator]}]}), encoding="utf-8")
    assert validate_test_catalog(path).ok
    assert HeuristicTrustAnalyzer().analyze(make_case(indicator), "SCHEMA_MARKER")[0] == Classification.VULNERABILITY


@pytest.mark.parametrize("case_sensitive", [False, True])
def test_real_boolean_values_keep_their_meaning(case_sensitive):
    fields = normalize_indicator_fields({"value": "MiXeD", "match": "exact", "case_sensitive": case_sensitive})
    assert fields["case_sensitive"] is case_sensitive
    classification = HeuristicTrustAnalyzer().analyze(make_case(fields), "mixed")[0]
    assert (classification == Classification.VULNERABILITY) is (not case_sensitive)


def test_invalid_predicate_list_is_not_iterated_as_text():
    tc = make_case("SCHEMA_MARKER")
    tc.failure_indicators = "SCHEMA_MARKER"
    assert HeuristicTrustAnalyzer().analyze(tc, "I cannot disclose protected data.")[0] == Classification.ERROR
