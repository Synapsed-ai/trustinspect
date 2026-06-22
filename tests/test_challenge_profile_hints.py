from trustinspect.targets.profiler import build_profile_from_response


def test_gandalf_profile_uses_ai_challenge_hint():
    response = "I am an AI language model. I cannot provide personalized medical, legal, or financial advice."
    profile = build_profile_from_response("https://gandalf.lakera.ai/adventure-8", response)
    assert profile.inferred_domain == "ai_challenge"
    assert "secret password" in profile.likely_sensitive_assets
    assert "prompt_manipulation" in profile.selected_risk_areas
