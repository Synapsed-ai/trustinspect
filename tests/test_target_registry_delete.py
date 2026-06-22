from pathlib import Path

import yaml

from trustinspect.targets.registry import TargetDefinition, archive_target, load_target_registry, normalize_optional_selector, save_local_target


def test_normalize_optional_selector_treats_null_as_none():
    assert normalize_optional_selector("null") is None
    assert normalize_optional_selector("None") is None
    assert normalize_optional_selector("-") is None
    assert normalize_optional_selector("#chat") == "#chat"


def test_archive_target_moves_yaml_file(tmp_path):
    local = tmp_path / "targets" / "local"
    local.mkdir(parents=True)
    path = local / "demo.yaml"
    path.write_text(yaml.safe_dump({"id": "demo", "name": "Demo", "url": "https://example.test"}), encoding="utf-8")

    registry = load_target_registry(builtins_dir=tmp_path / "targets" / "builtin", local_dir=local, legacy_builtins_dir=tmp_path / "examples" / "targets")
    target = registry.get("demo")
    assert target is not None
    dest = archive_target(target, disabled_dir=tmp_path / "targets" / "disabled")
    assert dest is not None
    assert dest.exists()
    assert not path.exists()
