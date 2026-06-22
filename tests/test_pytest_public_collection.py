from pathlib import Path


def test_pytest_ini_limits_collection_to_active_tests():
    pytest_ini = Path("pytest.ini")
    assert pytest_ini.exists()
    content = pytest_ini.read_text(encoding="utf-8")
    assert "testpaths = tests" in content
    assert "_archive" in content
    assert "reports" in content
