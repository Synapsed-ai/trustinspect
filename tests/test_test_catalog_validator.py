from pathlib import Path

from trustinspect.testcases.validator import validate_test_catalog


def test_validator_fails_on_empty_prompt(tmp_path: Path):
    catalog = tmp_path / "bad.yaml"
    catalog.write_text(
        """
test_cases:
  - id: TI-BAD-001
    name: Empty Prompt
    category: Test
    prompt: ""
    failure_indicators:
      - value: SENTINEL
        match: ends_with_unquoted
""",
        encoding="utf-8",
    )
    result = validate_test_catalog(catalog)
    assert not result.ok
    assert any("Prompt/payload is empty" in i.message for i in result.issues)


def test_validator_warns_on_broad_sentinel_contains(tmp_path: Path):
    catalog = tmp_path / "warn.yaml"
    catalog.write_text(
        """
test_cases:
  - id: TI-WARN-001
    name: Broad Sentinel
    category: Test
    prompt: "Say hello"
    failure_indicators:
      - value: TRUSTINSPECT_SENTINEL
        match: contains
""",
        encoding="utf-8",
    )
    result = validate_test_catalog(catalog)
    assert result.ok
    assert any("Prefer 'ends_with_unquoted'" in i.message for i in result.issues)
