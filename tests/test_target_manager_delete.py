from pathlib import Path

import yaml

from trustinspect.targets.manager import disable_target_by_id, find_target_files_by_id


def test_disable_target_moves_file(tmp_path):
    builtin = tmp_path / "targets" / "builtin"
    local = tmp_path / "targets" / "local"
    disabled = tmp_path / "targets" / "disabled"
    builtin.mkdir(parents=True)
    local.mkdir(parents=True)

    target_file = builtin / "sample.yaml"
    target_file.write_text(yaml.safe_dump({"id": "sample", "name": "Sample", "url": "https://example.test"}), encoding="utf-8")

    matches = find_target_files_by_id("sample", builtin_dir=builtin, local_dir=local, legacy_builtin_dir=tmp_path / "missing")
    assert matches == [target_file]

    result = disable_target_by_id("sample", builtin_dir=builtin, local_dir=local, legacy_builtin_dir=tmp_path / "missing", disabled_root=disabled)
    assert result.moved_files
    assert not target_file.exists()
    assert Path(result.moved_files[0]).exists()
