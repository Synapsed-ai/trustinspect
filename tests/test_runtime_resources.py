from pathlib import Path
from dataclasses import replace

import pytest
import yaml

from trustinspect import resources
from trustinspect.suites.registry import SUITES, resolve_suite_path
from trustinspect.testcases.loader import load_test_case_rows
from trustinspect.targets.registry import load_target_registry, save_local_target, archive_target


@pytest.mark.parametrize("suite", sorted(SUITES))
def test_suites_resolve_outside_checkout(suite, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = resolve_suite_path(suite)
    assert path.is_absolute()
    assert load_test_case_rows(path)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("relative", resources.RESOURCE_FILES)
def test_every_runtime_resource_exists(relative, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert resources.builtin_file(relative).is_file()


def test_suite_id_ignores_cwd_shadow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    shadow = tmp_path / SUITES["trustinspect-baseline"]
    shadow.parent.mkdir(parents=True)
    shadow.write_text("test_cases: []")
    assert resolve_suite_path("trustinspect-baseline") != shadow
    assert load_test_case_rows(resolve_suite_path("trustinspect-baseline"))


def test_explicit_missing_root_does_not_fall_back(tmp_path):
    with pytest.raises(FileNotFoundError):
        resolve_suite_path("trustinspect-baseline", project_root=tmp_path)


def test_unknown_resource_and_traversal_are_rejected():
    for key in ("../LICENSE", "/etc/passwd", "missing.yaml"):
        with pytest.raises(ValueError):
            resources.builtin_file(key)


def test_explicit_user_file_is_preserved(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "custom.yaml"
    path.write_text("test_cases: [{id: CUSTOM, payload: hello}]")
    assert load_test_case_rows(path)[0]["id"] == "CUSTOM"
    with pytest.raises(FileNotFoundError):
        load_test_case_rows(tmp_path / "missing.yaml")


@pytest.mark.parametrize("key", list(resources.RESOURCE_ALIASES))
def test_legacy_aitg_paths_are_aliases(key, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_test_case_rows(key)


def test_list_catalog_is_supported(tmp_path):
    p = tmp_path / "list.yaml"
    p.write_text("- id: LIST\n  payload: hello\n")
    assert load_test_case_rows(p)[0]["id"] == "LIST"


@pytest.mark.parametrize("data", ["not a catalog", "test_cases: hello", "test_cases: [1]"])
def test_invalid_catalog_shape_is_explicit(data, tmp_path):
    p = tmp_path / "invalid.yaml"
    p.write_text(data)
    with pytest.raises(ValueError):
        load_test_case_rows(p)


def test_dynamic_default_ignores_cwd_shadow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    shadow = tmp_path / "examples/dynamic_templates"
    shadow.mkdir(parents=True)
    result = resources.dynamic_template_directory("examples/dynamic_templates")
    assert result != shadow
    assert len(list(result.glob("*.yaml"))) == 8


def test_missing_custom_template_directory_is_explicit(tmp_path):
    with pytest.raises(FileNotFoundError):
        resources.dynamic_template_directory(tmp_path / "missing")


def test_bundled_data_wins_and_missing_files_do_not_fall_back(tmp_path, monkeypatch):
    package = tmp_path / "trustinspect"
    data = package / "_data"
    data.mkdir(parents=True)
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "setup.py").touch()
    key = resources.RESOURCE_FILES[0]
    source = tmp_path / key
    source.parent.mkdir(parents=True)
    source.write_text("source")
    monkeypatch.setattr(resources, "_PACKAGE_ROOT", package)
    with pytest.raises(FileNotFoundError):
        resources.builtin_file(key)
    installed = data / key
    installed.parent.mkdir(parents=True)
    installed.write_text("bundled")
    assert resources.builtin_file(key).read_text() == "bundled"


def test_builtin_disable_uses_workspace_override_without_mutation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    local = tmp_path / "overrides"
    registry = load_target_registry(local_dir=local)
    original = registry.get("promptairlines")
    assert original is not None
    src = Path(original.source_path)
    before = src.read_bytes()
    archived = archive_target(original, disabled_dir=tmp_path / "archive")
    assert archived and archived.is_file()
    assert src.read_bytes() == before
    assert load_target_registry(local_dir=local).get(original.id) is None
    save_local_target(replace(original, name="Local override", status="ready"), local_dir=local)
    assert load_target_registry(local_dir=local).get(original.id).name == "Local override"
    assert src.read_bytes() == before


def test_cli_default_and_adaptive_plan_work_outside_checkout(tmp_path, monkeypatch):
    import sys
    import trustinspect.cli as cli
    from trustinspect.core.models import Assessment
    monkeypatch.chdir(tmp_path)
    seen = []
    def capture(**kwargs):
        seen.append(kwargs["test_cases"])
        return Assessment(id="packaging-test", name="Packaging test", target=kwargs["target"])
    monkeypatch.setattr(cli, "_run_web_assessment", capture)
    common = ["--target-url", "https://example.invalid", "--input-selector", "#input", "--output-selector", "#output", "--quiet-ui", "--no-banner"]
    monkeypatch.setattr(sys, "argv", ["trustinspect", "scan-web", *common])
    cli.main()
    assert seen[-1]
    profile = tmp_path / "profile.yaml"
    profile.write_text(yaml.safe_dump({"name": "Test", "inferred_domain": "customer_support", "declared_capabilities": ["answer questions"]}))
    monkeypatch.setattr(sys, "argv", ["trustinspect", "adaptive-scan", *common, "--suite", "trustinspect-baseline", "--target-profile", str(profile), "--dynamic-per-static", "1"])
    cli.main()
    assert any(tc.metadata.get("source") == "adaptive" for tc in seen[-1])


def test_target_state_cannot_write_inside_package(tmp_path, monkeypatch):
    import trustinspect.targets.registry as registry_module
    monkeypatch.chdir(tmp_path)
    target = load_target_registry().get("promptairlines")
    forbidden = Path(registry_module.__file__).resolve().parents[1] / "forbidden-test-state"
    with pytest.raises(ValueError):
        save_local_target(target, local_dir=forbidden)
    with pytest.raises(ValueError):
        archive_target(target, disabled_dir=forbidden)
    assert not forbidden.exists()


def test_unsafe_target_filename_is_rejected(tmp_path):
    from trustinspect.targets.registry import TargetDefinition
    target = TargetDefinition(id="../outside", name="invalid", url="https://example.invalid")
    with pytest.raises(ValueError):
        save_local_target(target, local_dir=tmp_path)


@pytest.mark.parametrize("target_id", ["../outside", "nested/target", "nested\\target", ""])
def test_unsafe_target_archive_id_is_rejected(target_id, tmp_path):
    from trustinspect.targets.registry import TargetDefinition
    target = TargetDefinition(id=target_id, name="invalid", url="https://example.invalid")
    with pytest.raises(ValueError):
        archive_target(target, disabled_dir=tmp_path / "archive")
    assert not (tmp_path / "archive").exists()


def test_archive_does_not_overwrite_existing_destination(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import trustinspect.targets.registry as registry_module
    monkeypatch.chdir(tmp_path)
    target = load_target_registry().get("promptairlines")
    source = Path(target.source_path)
    original = source.read_bytes()
    monkeypatch.setattr(registry_module, "datetime", SimpleNamespace(utcnow=lambda: SimpleNamespace(strftime=lambda fmt: "fixed")))
    destination = tmp_path / "archive" / "fixed" / target.source_kind / source.name
    destination.parent.mkdir(parents=True)
    destination.write_text("preserved archive", encoding="utf-8")
    with pytest.raises(FileExistsError):
        archive_target(target, disabled_dir=tmp_path / "archive")
    assert destination.read_text() == "preserved archive"
    assert source.read_bytes() == original
    assert load_target_registry().get(target.id) is not None


def test_archive_rejects_symlink_destination(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import trustinspect.targets.registry as registry_module
    monkeypatch.chdir(tmp_path)
    target = load_target_registry().get("promptairlines")
    monkeypatch.setattr(registry_module, "datetime", SimpleNamespace(utcnow=lambda: SimpleNamespace(strftime=lambda fmt: "fixed")))
    destination = tmp_path / "archive" / "fixed" / target.source_kind / Path(target.source_path).name
    destination.parent.mkdir(parents=True)
    victim = tmp_path / "unrelated.yaml"
    victim.write_text("unchanged", encoding="utf-8")
    try:
        destination.symlink_to(victim)
    except OSError:
        pytest.skip("Symbolic links are not available in this environment")
    with pytest.raises(FileExistsError):
        archive_target(target, disabled_dir=tmp_path / "archive")
    assert victim.read_text() == "unchanged"
    assert load_target_registry().get(target.id) is not None
