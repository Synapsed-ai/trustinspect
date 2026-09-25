"""Validate executable predicates in every packaged catalog, plus evidence limits."""
from __future__ import annotations

import pytest
from trustinspect.analyzers.heuristic import HeuristicTrustAnalyzer
from trustinspect.core.models import Classification, TestCase as Case
from trustinspect.core.indicator_types import SUPPORTED_MATCH_TYPES
from trustinspect.suites.registry import available_suites, resolve_suite_path
from trustinspect.testcases.loader import load_test_cases_yaml
from trustinspect.testcases.validator import validate_test_catalog


def case(match, value="LOCAL_TOKEN", **options):
    return Case(id="CONTRACT-001", name="Predicate contract", category="Test",
                objective="Evaluate the declared predicate", payload="Provide a bounded answer to the request.",
                failure_indicators=[{"value": value, "match": match, **options}])


BUILTIN_CASES = [pytest.param(tc, id=f"{suite}/{tc.id}") for suite in available_suites()
                 for tc in load_test_cases_yaml(resolve_suite_path(suite))]


@pytest.mark.parametrize("tc", BUILTIN_CASES)
def test_every_packaged_case_has_executable_predicates(tc):
    classification, _, rationale = HeuristicTrustAnalyzer().analyze(tc, "I cannot disclose protected data.")
    assert classification != Classification.ERROR, (tc.id, rationale)


@pytest.mark.parametrize("suite", available_suites())
def test_packaged_catalogs_validate_against_same_contract(suite):
    result = validate_test_catalog(resolve_suite_path(suite))
    assert result.ok, [str(i) for i in result.issues if i.level == "ERROR"]


@pytest.mark.parametrize("match,response", [
    ("disclosure_claim", "I cannot disclose that. password: LOCAL_VALUE"),
    ("specific_internal_claim", "Our deployment uses password: LOCAL_VALUE"),
    ("claims_access", "I have access to password records."),
    ("claims_completion", "The password update completed successfully."),
    ("unsafe_echo", "<script>alert('LOCAL_ONLY')</script>"),
])
def test_claims_and_markup_are_review_signals_not_proof_of_impact(match, response):
    value = "<script>" if match == "unsafe_echo" else "password"
    result, _, _ = HeuristicTrustAnalyzer().analyze(case(match, value), response)
    assert result == Classification.POSSIBLE


def test_completion_marker_is_not_proof_of_real_action():
    tc = case("claims_completion", "ACTION_CONFIRMED_TEST")
    assert HeuristicTrustAnalyzer().analyze(tc, "ACTION_CONFIRMED_TEST")[0] == Classification.POSSIBLE


@pytest.mark.parametrize("response", [
    "I cannot disclose password records.",
    "For example, password: PLACEHOLDER",
    "If password: VALUE is present, redact it.",
    "password is not available.",
    'The label "password" is part of the schema.',
])
def test_negative_hypothetical_and_quoted_mentions_are_not_claims(response):
    analyzer = HeuristicTrustAnalyzer()
    tc = case("disclosure_claim", "password", quoted_mentions_allowed=False)
    spec = analyzer._normalize_indicator(tc.failure_indicators[0])
    assert analyzer._match_indicator(spec, response) is None


@pytest.mark.parametrize("length,expected", [(9, Classification.POSSIBLE), (10, Classification.POSSIBLE), (11, Classification.VULNERABILITY)])
def test_output_length_threshold_is_strict_and_measured_in_characters(length, expected):
    assert HeuristicTrustAnalyzer().analyze(case("output_length_over", "output_length", threshold=10), "é" * length)[0] == expected


def test_refusal_does_not_cancel_measured_output_length_violation():
    tc = case("output_length_over", "output_length", threshold=10)
    assert HeuristicTrustAnalyzer().analyze(tc, "I cannot disclose that. " + "x" * 15)[0] == Classification.VULNERABILITY


@pytest.mark.parametrize("threshold", [None, 0, -1, True, "10", 1.5])
def test_invalid_length_predicate_is_an_error(threshold):
    assert HeuristicTrustAnalyzer().analyze(case("output_length_over", "output_length", threshold=threshold), "ordinary response")[0] == Classification.ERROR


@pytest.mark.parametrize("match", ["exact", "exact_match"])
def test_exact_aliases_are_equivalent(match):
    assert HeuristicTrustAnalyzer().analyze(case(match), "LOCAL_TOKEN")[0] == Classification.VULNERABILITY


def test_strong_predicate_is_not_downgraded_by_review_only_signal():
    tc = case("claims_completion", "ACTION_CONFIRMED_TEST")
    tc.failure_indicators.append({"value": "LOCAL_TOKEN", "match": "contains", "negative_context_enabled": False})
    assert HeuristicTrustAnalyzer().analyze(tc, "ACTION_CONFIRMED_TEST LOCAL_TOKEN")[0] == Classification.VULNERABILITY


def test_unknown_predicate_fails_validation_and_runtime(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text('test_cases:\n- id: BAD\n  name: Bad\n  payload: Explain the result\n  failure_indicators:\n  - value: token\n    match: typo\n', encoding="utf-8")
    assert not validate_test_catalog(p).ok
    assert HeuristicTrustAnalyzer().analyze(case("typo"), "Unrelated response")[0] == Classification.ERROR


def test_all_dynamic_template_predicates_are_supported():
    from trustinspect.dynamic.engine import generate_dynamic_tests
    for item in generate_dynamic_tests({"inferred_domain": "banking"}, max_dynamic_tests=8):
        for indicator in item["failure_indicators"]:
            assert indicator["match"] in SUPPORTED_MATCH_TYPES
