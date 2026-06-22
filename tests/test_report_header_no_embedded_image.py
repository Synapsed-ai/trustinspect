from pathlib import Path


def test_report_template_has_lightweight_css_header_and_no_embedded_image():
    template = Path("trustinspect/reporting/templates/assessment_report.html.j2").read_text(encoding="utf-8")
    assert "data:image" not in template
    assert "base64" not in template.lower()
    assert "TRUSTINSPECT" in template or "ti-logo" in template
    assert ("ti-cover" in template) or ("ti-ascii-hero" in template) or ("ti-report-cover" in template)
