from pathlib import Path


def test_pytest_config_ignores_archive_and_runtime_outputs():
    config = Path("pytest.ini")
    assert config.exists(), "pytest.ini must exist for public release test collection hygiene"
    text = config.read_text(encoding="utf-8")
    assert "testpaths = tests" in text
    assert "_archive" in text
    assert "reports" in text
    assert "profiles" in text
    assert "generated_tests" in text
