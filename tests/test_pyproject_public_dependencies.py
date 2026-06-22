from pathlib import Path


def test_pyproject_declares_rich_dependency():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "rich" in text.lower()
