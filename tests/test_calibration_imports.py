def test_calibration_module_imports():
    import trustinspect.interactive.calibration as calibration
    assert hasattr(calibration, "calibrate_target_selectors")


def test_normalize_null_selectors():
    from trustinspect.targets.registry import normalize_optional_selector
    assert normalize_optional_selector("null") is None
    assert normalize_optional_selector("none") is None
    assert normalize_optional_selector("-") is None
    assert normalize_optional_selector("#chat") == "#chat"
