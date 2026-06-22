from trustinspect.core.models import Assessment, Target
from trustinspect.reporting.html_report import HtmlReporter


def test_adaptive_metadata_reaches_report_summary(tmp_path):
    target = Target(
        id="target-promptairlines",
        name="promptairlines.com",
        url="https://promptairlines.com",
        target_type="web-ui",
    )
    assessment = Assessment(
        id="assessment-test-001",
        name="Test Adaptive Assessment",
        target=target,
        observations=[],
        findings=[],
        metadata={
            "assessment_mode": "adaptive",
            "generation_strategy": "deterministic-template",
            "baseline_tests_count": 8,
            "adaptive_tests_count": 8,
            "target_profile": {
                "declared_identity": "Prompt Airlines assistant",
                "inferred_domain": "travel",
                "interaction_style": "customer_support",
                "declared_capabilities": ["booking support"],
                "declared_boundaries": ["travel only"],
                "selected_risk_areas": ["hidden_instruction_following"],
                "likely_sensitive_assets": ["passenger emails"],
            },
            "generated_test_plan": [
                {
                    "id": "TI-CTX-001",
                    "name": "Domain Boundary Override",
                    "category": "Prompt Manipulation / Domain Boundary",
                    "risk_area": "domain_boundary_escape",
                    "reason": "Selected because the target declared a travel/customer support boundary.",
                }
            ],
        },
    )
    assessment.complete()

    output = tmp_path / "report.html"
    HtmlReporter().render(assessment, output)
    html = output.read_text(encoding="utf-8")

    assert "Assessment Mode" in html
    assert "adaptive" in html
    assert "Target Capability Profile" in html
    assert "Generated Test Plan" in html
    assert "TI-CTX-001" in html
    assert "passenger emails" in html
