from trustinspect.core.models import (
    Assessment,
    Classification,
    EvidenceItem,
    EvidenceType,
    Observation,
    Target,
    TestCase,
)
from trustinspect.reporting.html_report import HtmlReporter


def test_aitg_report_infers_suite_and_uses_official_layers(tmp_path):
    target = Target(id="demo", name="127.0.0.1", url="http://127.0.0.1:8080/")
    tc = TestCase(
        id="AITG-APP-03-DYN-001",
        name="Sensitive data dynamic variant",
        category="Privacy / Sensitive Data",
        objective="test",
        payload="prompt",
        metadata={
            "source": "dynamic",
            "parent_static_test_id": "AITG-APP-03",
            "aitg_layer": "AI Application Testing",
        },
    )
    evp = EvidenceItem(id="p", evidence_type=EvidenceType.PROMPT, value="prompt")
    evr = EvidenceItem(id="r", evidence_type=EvidenceType.RESPONSE, value="bad response")
    obs = Observation(
        id="o1",
        target=target,
        test_case=tc,
        classification=Classification.VULNERABILITY,
        confidence=0.95,
        evidence=[evp, evr],
        rationale="matched indicator",
        metadata={"execution_time_seconds": 0.42},
    )
    assessment = Assessment(
        id="a1",
        name="TrustInspect Web UI Assessment",
        target=target,
        observations=[obs],
        findings=[],
        started_at="2026-06-16T10:00:00+00:00",
        completed_at="2026-06-16T10:00:05+00:00",
        metadata={
            "assessment_mode": "adaptive",
            "generated_test_plan": [
                {
                    "id": "AITG-APP-03-DYN-001",
                    "name": "Sensitive data dynamic variant",
                    "parent_static_test_id": "AITG-APP-03",
                    "generation_reason": "Generated for APP sensitive data test.",
                }
            ],
        },
    )
    output = tmp_path / "report.html"
    HtmlReporter().render(assessment, output)
    html = output.read_text(encoding="utf-8")

    assert "OWASP AI Testing Guide — Light" in html
    assert "OWASP AITG Impact Overview" in html
    assert "AI Application Testing" in html
    assert "Generated Dynamic Tests by OWASP AITG Layer" in html
    assert "Findings Summary" not in html
    assert "Primary Impacted Dimensions" not in html
    assert "data:image" not in html
    assert "5s" in html
