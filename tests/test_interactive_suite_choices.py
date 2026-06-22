from trustinspect.interactive import launcher


def test_interactive_suite_choices_include_aitg_light_and_full():
    ids = [s["id"] for s in launcher.SUITES]
    assert "owasp-aitg-light" in ids
    assert "owasp-aitg-full" in ids
    labels = "\n".join(s["label"] for s in launcher.SUITES)
    assert "planned" not in labels.lower()
