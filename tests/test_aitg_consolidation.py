from dataclasses import dataclass, field
from pathlib import Path

from trustinspect.reporting.suite_metadata import enrich_assessment_suite_metadata


@dataclass
class FakeTestCase:
    id: str
    name: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class FakeObservation:
    test_case: FakeTestCase
    classification: str = "SAFE"


@dataclass
class FakeAssessment:
    observations: list
    metadata: dict = field(default_factory=dict)


def test_suite_metadata_infers_aitg_light():
    assessment = FakeAssessment(observations=[FakeObservation(FakeTestCase("AITG-APP-01"))])
    enrich_assessment_suite_metadata(assessment)
    assert assessment.metadata["suite_id"] == "owasp-aitg-light"
    assert assessment.metadata["suite_display_name"] == "OWASP AI Testing Guide — Light"


def test_report_template_is_lightweight_and_aitg_oriented():
    template = Path("trustinspect/reporting/templates/assessment_report.html.j2").read_text(encoding="utf-8")
    assert "data:image/png;base64" not in template
    assert "Findings Summary" not in template
    assert "Findings Impact Summary" not in template
    assert "OWASP AITG Impact Overview" in template
    assert "Generated Dynamic Tests by OWASP AITG Layer" in template
