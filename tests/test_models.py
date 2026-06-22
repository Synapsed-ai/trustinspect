from trustinspect.cli import build_demo_assessment


def test_demo_assessment_has_finding():
    assessment = build_demo_assessment()
    assert assessment.findings
    assert assessment.findings[0].trustworthiness_dimension
