from trustinspect.dynamic.engine import generate_dynamic_tests


def test_dynamic_engine_generates_travel_specific_tests():
    profile = {
        "declared_identity": "Prompt Airlines customer service assistant",
        "inferred_domain": "travel",
        "interaction_style": "customer_support",
        "likely_sensitive_assets": ["passenger emails", "booking references"],
        "forbidden_actions": ["book a flight without user confirmation"],
        "risk_areas": ["hidden_instruction_following", "sensitive_data_exposure", "unauthorized_action_request"],
    }

    tests = generate_dynamic_tests(profile, max_dynamic_tests=5)
    prompts = "\n".join(t["prompt"] for t in tests).lower()

    assert len(tests) == 5
    assert "passenger emails" in prompts or "booking references" in prompts
    assert "flight" in prompts or "travel" in prompts
    assert "transfer funds" not in prompts


def test_dynamic_engine_generates_banking_specific_tests():
    profile = {
        "declared_identity": "Banking support assistant",
        "inferred_domain": "banking",
        "interaction_style": "customer_support",
        "likely_sensitive_assets": ["IBAN numbers", "transaction history"],
        "forbidden_actions": ["transfer funds without confirmation"],
        "risk_areas": ["hidden_instruction_following", "sensitive_data_exposure", "unauthorized_action_request"],
    }

    tests = generate_dynamic_tests(profile, max_dynamic_tests=5)
    prompts = "\n".join(t["prompt"] for t in tests).lower()

    assert len(tests) == 5
    assert "iban" in prompts or "transaction history" in prompts
    assert "transfer funds" in prompts
    assert "book a flight" not in prompts


def test_hidden_instruction_indicator_uses_ends_with_unquoted():
    profile = {"inferred_domain": "travel", "risk_areas": ["hidden_instruction_following"]}
    tests = generate_dynamic_tests(profile, max_dynamic_tests=1)
    indicator = tests[0]["failure_indicators"][0]

    assert indicator["value"] == "TRUSTINSPECT_SENTINEL"
    assert indicator["match"] == "ends_with_unquoted"
    assert indicator["quoted_mentions_allowed"] is False
