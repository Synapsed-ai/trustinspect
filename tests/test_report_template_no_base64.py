from pathlib import Path


def test_report_template_does_not_embed_base64_png_header():
    template = Path("trustinspect/reporting/templates/assessment_report.html.j2")
    assert template.exists()
    text = template.read_text(encoding="utf-8")
    assert "data:image/png;base64" not in text
    assert "TRUSTINSPECT" in text
    assert "Executive Summary" in text
