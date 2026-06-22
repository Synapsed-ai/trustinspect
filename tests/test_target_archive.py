from pathlib import Path
from trustinspect.targets.registry import TargetDefinition, archive_target


def test_archive_target_moves_yaml(tmp_path, monkeypatch):
    targets_dir = tmp_path / "targets" / "local"
    targets_dir.mkdir(parents=True)
    path = targets_dir / "sample.yaml"
    path.write_text("id: sample\nname: Sample\nurl: https://example.test\ninput_selector: '#i'\noutput_selector: '#o'\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    target = TargetDefinition(id="sample", name="Sample", url="https://example.test", input_selector="#i", output_selector="#o")
    archived = archive_target(target)
    assert archived is not None
    assert archived.exists()
    assert not path.exists()
    assert "targets/disabled" in str(archived)
