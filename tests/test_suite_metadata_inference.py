from dataclasses import dataclass, field

from trustinspect.reporting.suite_metadata import enrich_assessment_suite_metadata


@dataclass
class FakeTestCase:
    id: str
    name: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class FakeObservation:
    test_case: FakeTestCase


@dataclass
class FakeAssessment:
    observations: list
    metadata: dict = field(default_factory=dict)


def test_infers_aitg_light_from_test_ids():
    assessment = FakeAssessment(observations=[FakeObservation(FakeTestCase("AITG-APP-01"))])
    enrich_assessment_suite_metadata(assessment)
    assert assessment.metadata["suite_id"] == "owasp-aitg-light"
    assert "AI Testing Guide" in assessment.metadata["suite_display_name"]


def test_preserves_explicit_suite():
    assessment = FakeAssessment(
        observations=[FakeObservation(FakeTestCase("AITG-APP-01"))],
        metadata={"suite": "owasp-aitg-full"},
    )
    enrich_assessment_suite_metadata(assessment)
    assert assessment.metadata["suite_id"] == "owasp-aitg-full"
    assert "Full" in assessment.metadata["suite_display_name"]
