from trustinspect.dynamic.risk_mapper import normalize_target_profile


def test_profile_normalizer_infers_travel_assets_and_risks():
    profile = normalize_target_profile({
        "declared_identity": "I help Prompt Airlines members book tickets and view existing flight tickets.",
        "profiling_response": "I cannot disclose personal information or offer free flights.",
    })

    assert profile["inferred_domain"] == "travel"
    assert "passenger emails" in profile["likely_sensitive_assets"]
    assert "hidden_instruction_following" in profile["risk_areas"]
    assert "unauthorized_action_request" in profile["risk_areas"]
