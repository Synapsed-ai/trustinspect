from trustinspect.core.models import (
    Assessment,
    Classification,
    EvidenceItem,
    EvidenceType,
    Finding,
    Observation,
    Severity,
    Target,
    TestCase,
)
from trustinspect.reporting.html_report import HtmlReporter


def test_aitg_report_uses_visual_summary_and_official_layers(tmp_path):
    target = Target(id="demo", name="127.0.0.1", url="http://127.0.0.1:8080/")
    tc = TestCase(
        id="AITG-DAT-05",
        name="Testing for Data Minimization and Consent",
        category="Data Minimization",
        objective="test",
        payload="prompt",
        metadata={"source": "static", "aitg_layer": "AI Data Testing"},
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
    )
    finding = Finding(
        id="TI-AITG-DAT-05-001",
        title="Data minimization issue",
        severity=Severity.HIGH,
        confidence=0.95,
        trustworthiness_dimension="Privacy",
        observation_id="o1",
        description="desc",
        impact="impact",
        remediation="remediation",
        evidence=[evp, evr],
        metadata={"source_test": "AITG-DAT-05"},
    )
    assessment = Assessment(
        id="a1",
        name="TrustInspect Web UI Assessment",
        target=target,
        observations=[obs],
        findings=[finding],
        metadata={"suite_id": "owasp-aitg-light", "suite_display_name": "OWASP AI Testing Guide — Light"},
    )
    assessment.complete()
    output = tmp_path / "report.html"
    HtmlReporter().render(assessment, output)
    html = output.read_text(encoding="utf-8")
    assert "OWASP AITG Impact Overview" in html
    assert "AI Data Testing" in html
    assert "Findings Summary" not in html
    assert "Primary Impacted Dimensions" not in html
    assert "Robustness" not in html or "trustworthiness_dimension" not in html
    assert "Generated Dynamic Tests by OWASP AITG Layer" in html or "OWASP AITG Coverage Matrix" in html
    assert "data:image" not in html
