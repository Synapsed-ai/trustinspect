"""Build-hook regressions: the source catalog remains the only source of truth."""
import importlib.util
import json
from pathlib import Path

import pytest
import setuptools
from setuptools.command.build_py import build_py
from setuptools.dist import Distribution


@pytest.fixture
def build_module(monkeypatch):
    source = Path(__file__).resolve().parents[1] / "setup.py"
    monkeypatch.setattr(setuptools, "setup", lambda **kwargs: None)
    spec = importlib.util.spec_from_file_location("ti_build_regression", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_manifest(root, paths):
    (root / "trustinspect").mkdir(exist_ok=True)
    (root / "trustinspect/_resource_manifest.json").write_text(json.dumps(paths), encoding="utf-8")


def test_missing_runtime_resource_fails_build(build_module, tmp_path, monkeypatch):
    fixture_manifest(tmp_path, ["missing.yaml"])
    monkeypatch.setattr(build_module, "ROOT", tmp_path)
    with pytest.raises(FileNotFoundError):
        build_module.resource_files()


@pytest.mark.parametrize("paths", [["../outside.yaml"], ["a.yaml", "a.yaml"], "not-a-list"])
def test_invalid_manifest_fails_build(paths, build_module, tmp_path, monkeypatch):
    fixture_manifest(tmp_path, paths)
    monkeypatch.setattr(build_module, "ROOT", tmp_path)
    with pytest.raises(ValueError):
        build_module.resource_files()


def test_stale_build_data_is_not_carried_into_next_wheel(build_module, tmp_path, monkeypatch):
    fixture_manifest(tmp_path, ["resource.yaml"])
    (tmp_path / "resource.yaml").write_text("expected", encoding="utf-8")
    monkeypatch.setattr(build_module, "ROOT", tmp_path)
    monkeypatch.setattr(build_py, "run", lambda self: None)
    command = build_module.BuildWithRuntimeData(Distribution())
    command.ensure_finalized()
    command.build_lib = str(tmp_path / "build")
    command.editable_mode = False
    stale = Path(command.build_lib) / "trustinspect/_data/private.env"
    stale.parent.mkdir(parents=True)
    stale.write_text("synthetic stale content", encoding="utf-8")
    command.run()
    assert not stale.exists()
    assert (stale.parent / "resource.yaml").read_text() == "expected"


def test_editable_build_does_not_write_bundled_data(build_module, tmp_path, monkeypatch):
    monkeypatch.setattr(build_py, "run", lambda self: None)
    command = build_module.BuildWithRuntimeData(Distribution())
    command.ensure_finalized()
    command.build_lib = str(tmp_path / "build")
    command.editable_mode = True
    command.run()
    assert not Path(command.build_lib).exists()


@pytest.fixture
def distribution_verifier():
    source = Path(__file__).resolve().parents[1] / "scripts/maintenance/verify_installed_distribution.py"
    spec = importlib.util.spec_from_file_location("ti_distribution_verifier", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_isolated_python_command_preserves_spaces_and_explicit_utf8(distribution_verifier):
    command = distribution_verifier.isolated_python_command(
        "path with spaces/python", "script with spaces.py"
    )
    assert command == ["path with spaces/python", "-I", "-B", "-X", "utf8", "script with spaces.py"]


def test_isolated_python_ignores_hostile_encoding_environment(distribution_verifier, tmp_path):
    import os
    import subprocess
    import sys
    env = dict(os.environ, PYTHONUTF8="0", PYTHONIOENCODING="ascii", PYTHONPATH=str(tmp_path))
    code = "import sys; assert sys.flags.isolated; assert sys.flags.utf8_mode; assert sys.dont_write_bytecode; print('\\u2588\\u2014\\u2713')"
    completed = subprocess.run(
        distribution_verifier.isolated_python_command(sys.executable, "-c", code),
        cwd=tmp_path, env=env, capture_output=True, check=True,
    )
    assert completed.stdout.decode("utf-8").strip() == "\u2588\u2014\u2713"
