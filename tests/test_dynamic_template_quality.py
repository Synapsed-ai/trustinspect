from pathlib import Path
import yaml


def test_dynamic_templates_are_valid_yaml_and_have_required_fields():
    template_dir = Path("examples/dynamic_templates")
    assert template_dir.exists()
    for path in sorted(template_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["template_id"]
        assert data["id"].startswith("TI-DYN-")
        assert data["risk_area"]
        assert data["prompt_template"].strip()
        assert data["expected_behavior"].strip()
        assert data["failure_indicators"]
        assert data["generation_reason_template"].strip()


def test_hidden_instruction_uses_precise_indicator_semantics():
    data = yaml.safe_load(Path("examples/dynamic_templates/01_hidden_instruction.yaml").read_text(encoding="utf-8"))
    indicator = data["failure_indicators"][0]
    assert indicator["match"] == "ends_with_unquoted"
    assert indicator["quoted_mentions_allowed"] is False


def test_unsafe_output_template_uses_safe_plain_text_sentinel():
    data = yaml.safe_load(Path("examples/dynamic_templates/06_unsafe_output_echo.yaml").read_text(encoding="utf-8"))
    assert "TRUSTINSPECT_XSS" in data["unsafe_echo_payload"]
    assert data["failure_indicators"][0]["match"] == "unsafe_echo"
