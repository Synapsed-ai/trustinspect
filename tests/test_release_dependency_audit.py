"""Release manifests retain transitive versions and reject malformed inputs."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("release_audit", Path(__file__).resolve().parents[1] / "tools/release_dependency_audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def item(name="Example_Package", version="1.2.3", digest="a" * 64):
    return {"metadata": {"name": name, "version": version, "requires_dist": ["transitive>=1"]},
            "requested": False, "download_info": {"archive_info": {"hashes": {"sha256": digest}}}}


def test_transitive_entries_are_not_filtered():
    result = audit.pins_from_report({"install": [item(), item("transitive")]})
    assert [r["name"] for r in result] == ["example-package", "transitive"]
    assert all(r["version"] == "1.2.3" for r in result)


def test_local_project_not_submitted_to_public_package_database():
    project = {"metadata": {"name": "trustinspect"}}
    assert len(audit.pins_from_report({"install": [project, item()]})) == 1


@pytest.mark.parametrize("entry", [item(digest="bad"), item(version="1.0\nother==1"), item(name="bad/name")])
def test_invalid_lock_inputs_fail(entry):
    with pytest.raises(ValueError):
        audit.pins_from_report({"install": [entry]})


def test_empty_audit_is_not_success():
    with pytest.raises(ValueError):
        audit.pins_from_report({"install": []})


def test_duplicate_canonical_names_fail():
    with pytest.raises(ValueError):
        audit.pins_from_report({"install": [item(), item("example-package")]})


def test_metadata_reader_explicitly_uses_utf8(tmp_path, monkeypatch):
    path = tmp_path / "metadata.json"
    path.write_text('{"text":"città — 日本語"}', encoding="utf-8")
    original = Path.read_text
    def checked(self, *args, **kwargs):
        assert kwargs.get("encoding") == "utf-8"
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", checked)
    assert audit.read_json(path)["text"] == "città — 日本語"
