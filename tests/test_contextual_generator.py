from trustinspect.targets.profile import TargetCapabilityProfile
from trustinspect.testcases.generator import generate_contextual_tests


def _field(test_case, name, default=None):
    if isinstance(test_case, dict):
        return test_case.get(name, default)
    return getattr(test_case, name, default)


def _payload(test_case):
    return _field(test_case, "payload") or _field(test_case, "prompt") or ""


def test_generator_creates_contextual_tests_for_travel_profile():
    profile = TargetCapabilityProfile(
        target_id="promptairlines",
        name="PromptAirlines",
        url="https://promptairlines.com/",
        inferred_domain="travel",
        interaction_style="customer_support",
        likely_sensitive_assets=["passenger emails", "booking references"],
        selected_risk_areas=["hidden_instruction_following", "sensitive_data_exposure"],
    )
    tests = generate_contextual_tests(profile, max_tests=8)
    assert len(tests) == 8
    payloads = [_payload(t) for t in tests]
    assert any("passenger emails" in p or "booking references" in p for p in payloads)
    assert any("TRUSTINSPECT_SENTINEL" in p or "SENTINEL" in p for p in payloads)


def test_generator_respects_max_tests():
    profile = TargetCapabilityProfile(
        target_id="demo",
        name="Demo",
        url="https://example.test/",
        inferred_domain="generic",
        interaction_style="assistant",
    )
    assert len(generate_contextual_tests(profile, max_tests=3)) == 3
