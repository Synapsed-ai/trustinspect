from pathlib import Path


def test_runtime_code_does_not_disable_chrome_sandbox():
    bad_arg = "--" + "no-sandbox"
    paths = [
        Path("trustinspect/interactive/calibration.py"),
        Path("trustinspect/scanners/web_ui/selenium_scanner.py"),
        Path("trustinspect/scanners/web_ui/auto_selector.py"),
    ]
    for path in paths:
        assert path.exists(), f"Missing expected runtime file: {path}"
        assert bad_arg not in path.read_text(encoding="utf-8"), f"{path} still disables Chrome sandbox"


def test_dom_snapshot_is_saved_as_text_artifact():
    path = Path("trustinspect/scanners/web_ui/selenium_scanner.py")
    text = path.read_text(encoding="utf-8")
    assert "_dom.html.txt" in text
    assert "_dom.html\"" not in text
    assert "_dom.html'" not in text
