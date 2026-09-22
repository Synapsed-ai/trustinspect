#!/usr/bin/env python3
"""Verify a built wheel in a fresh venv, outside the source checkout.

Run after `python -m build`: python scripts/maintenance/verify_installed_distribution.py
Requires network access only for installation of declared public dependencies.
No browser, external AI target, API credentials, release or publication is used.
"""
from __future__ import annotations

import argparse
from email.parser import Parser
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import venv
import zipfile


PROBE = r'''
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import sysconfig
from unittest.mock import patch

import yaml
import trustinspect
from trustinspect import resources
from trustinspect.cli import _load_test_cases
from trustinspect.dynamic.engine import DynamicTestEngine
from trustinspect.dynamic.per_static import generate_dynamic_tests_for_static_suite
from trustinspect.suites.registry import SUITES, resolve_suite_path
from trustinspect.targets.registry import load_target_registry, archive_target, save_local_target
from trustinspect.testcases.loader import load_test_case_rows

installed = Path(trustinspect.__file__).resolve().parent
assert installed.is_relative_to(Path(sys.prefix).resolve()), (installed, sys.prefix)
assert sys.prefix != sys.base_prefix, "Probe must execute in a venv"
assert not Path.cwd().is_relative_to(installed)
expectations = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for relative, expected in expectations.items():
    actual = hashlib.sha256((installed.parent / relative).read_bytes()).hexdigest()
    assert actual == expected, relative

assert len(resources.RESOURCE_FILES) == 18
for key in resources.RESOURCE_FILES:
    assert resources.builtin_file(key).is_relative_to(installed)
counts = {sid: len(load_test_case_rows(resolve_suite_path(sid))) for sid in SUITES}
assert len(counts) == 5 and all(counts.values()), counts
assert _load_test_cases("examples/test_cases/owasp_light_full.yaml")
for alias in resources.RESOURCE_ALIASES:
    assert _load_test_cases(alias)

# Default suite IDs are not shadowed by similarly named cwd files.
shadow = Path(SUITES["trustinspect-baseline"])
shadow.parent.mkdir(parents=True)
shadow.write_text("test_cases: []", encoding="utf-8")
assert load_test_case_rows(resolve_suite_path("trustinspect-baseline"))
custom = Path("custom.yaml")
custom.write_text("test_cases: [{id: CUSTOM, payload: hello}]", encoding="utf-8")
assert _load_test_cases(custom)[0].id == "CUSTOM"
try:
    _load_test_cases("does-not-exist.yaml")
except FileNotFoundError:
    pass
else:
    raise AssertionError("Missing custom catalog did not fail")

profile = {"name": "Packaging fixture", "inferred_domain": "customer_support", "declared_capabilities": ["answer support questions"], "declared_boundaries": ["do not disclose private information"], "likely_sensitive_assets": ["account identifiers"]}
generated = DynamicTestEngine().generate(profile, max_dynamic_tests=4)
assert 0 < len(generated) <= 4
static = _load_test_cases(resolve_suite_path("trustinspect-baseline"))[:2]
variants = generate_dynamic_tests_for_static_suite(static_tests=static, target_profile=profile, dynamic_tests_per_static=1)
assert variants

registry = load_target_registry()
assert len(registry.list()) == 3
original = registry.get("promptairlines")
assert original
source = Path(original.source_path)
before = source.read_bytes()
archive = archive_target(original)
assert archive and archive.is_file()
assert source.read_bytes() == before
assert load_target_registry().get(original.id) is None
from dataclasses import replace
save_local_target(replace(original, status="ready", name="Workspace override"))
assert load_target_registry().get(original.id).name == "Workspace override"
assert source.read_bytes() == before

# Exercise the actual CLI parser/orchestrator for all suites. Only browser
# execution is replaced: this is explicitly not a Selenium end-to-end test.
import trustinspect.cli as cli
from trustinspect.core.models import Assessment
profile_path = Path("profile.yaml")
profile_path.write_text(yaml.safe_dump(profile), encoding="utf-8")
seen = []
def capture(**kwargs):
    seen.append(kwargs["test_cases"])
    return Assessment(id="wheel-check", name="Wheel check", target=kwargs["target"])
common = ["--target-url", "https://example.invalid", "--input-selector", "#input", "--output-selector", "#output", "--quiet-ui", "--no-banner"]
plans = [["scan-web", *common]]
plans += [["scan-web", *common, "--suite", sid] for sid in SUITES]
plans += [["adaptive-scan", *common, "--suite", "trustinspect-baseline", "--target-profile", str(profile_path), "--dynamic-per-static", "1"]]
with patch.object(cli, "_run_web_assessment", capture):
    for args in plans:
        with patch.object(sys, "argv", ["trustinspect", *args]):
            cli.main()
        assert seen[-1]
assert any(t.metadata.get("source") == "adaptive" for t in seen[-1])

# Resource and source bytes must remain unchanged by generation/archive/reporting.
for relative, expected in expectations.items():
    assert hashlib.sha256((installed.parent / relative).read_bytes()).hexdigest() == expected, relative
print("INSTALLED_PROBE=" + json.dumps({"installed_module": str(installed), "python": sys.version.split()[0], "suites": counts, "resources": len(resources.RESOURCE_FILES), "dynamic_tests": len(generated), "per_static_variants": len(variants), "cli_plans_without_browser": len(plans), "targets": len(registry.list()), "immutable_package_files": len(expectations)}))
'''


def execute(command, cwd, env, timeout=300):
    result = subprocess.run(command, cwd=cwd, env=env, text=True, encoding="utf-8",
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    print(result.stdout, end="", flush=True)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}")
    return result.stdout


def inspect_wheel(wheel: Path, source_root: Path) -> dict:
    with zipfile.ZipFile(wheel) as archive:
        files = [n for n in archive.namelist() if not n.endswith("/")]
        assert all(n.startswith("trustinspect/") or n.split("/")[0].startswith("trustinspect-") and n.split("/")[0].endswith(".dist-info") for n in files), "Unexpected top-level wheel files"
        assert len(files) == len(set(files)), "Duplicate wheel members"
        assert all(not PurePosixPath(n).is_absolute() and ".." not in PurePosixPath(n).parts and "\\" not in n for n in files), "Unsafe wheel member paths"
        manifest = json.loads(archive.read("trustinspect/_resource_manifest.json"))
        expected = {"trustinspect/_data/" + p for p in manifest}
        actual = {n for n in files if n.startswith("trustinspect/_data/")}
        assert actual == expected, {"extra": sorted(actual-expected), "missing": sorted(expected-actual)}
        for relative in manifest:
            assert archive.read("trustinspect/_data/" + relative) == (source_root / relative).read_bytes(), relative
        metadata_name = next(n for n in files if n.endswith(".dist-info/METADATA"))
        metadata = Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
        assert metadata["Name"] == "trustinspect"
        assert metadata["License-Expression"] == "Apache-2.0"
        for name in ("LICENSE", "NOTICE"):
            assert any(n.endswith(".dist-info/licenses/"+name) for n in files), name
        entry = next(n for n in files if n.endswith(".dist-info/entry_points.txt"))
        assert "trustinspect = trustinspect.cli:main" in archive.read(entry).decode()
        for name in files:
            if name.startswith("trustinspect/") and not name.startswith("trustinspect/_data/"):
                assert name.endswith((".py", ".j2")) or name == "trustinspect/_resource_manifest.json", name
                assert archive.read(name) == (source_root / name).read_bytes(), name
        hashes = {n: hashlib.sha256(archive.read(n)).hexdigest() for n in files if n.startswith("trustinspect/")}
    return {"hashes": hashes, "resource_count": len(manifest), "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    source = args.source_root.resolve()
    candidates = sorted((source / "dist").glob("*.whl"))
    if args.wheel is None and len(candidates) != 1:
        raise SystemExit("Specify --wheel or provide exactly one wheel in dist/")
    wheel = (args.wheel or candidates[0]).resolve()
    checked = inspect_wheel(wheel, source)
    env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHONHOME"}}
    env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PIP_DISABLE_PIP_VERSION_CHECK="1", NO_COLOR="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    with tempfile.TemporaryDirectory(prefix="trustinspect wheel check ") as temporary:
        root = Path(temporary)
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(environment)
        scripts = environment / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        cli = scripts / ("trustinspect.exe" if os.name == "nt" else "trustinspect")
        workspace = root / "unrelated workspace"
        workspace.mkdir()
        execute([str(python), "-I", "-m", "pip", "install", "--no-compile", str(wheel)], workspace, env)
        execute([str(python), "-I", "-m", "pip", "check"], workspace, env)
        expected = root / "expected.json"
        expected.write_text(json.dumps(checked["hashes"]), encoding="utf-8")
        probe = root / "installed_probe.py"
        probe.write_text(PROBE, encoding="utf-8")
        output = execute([str(python), "-I", str(probe), str(expected)], workspace, env)
        marker = next(line for line in output.splitlines() if line.startswith("INSTALLED_PROBE="))
        summary = json.loads(marker.split("=", 1)[1])
        execute([str(cli), "--help"], workspace, env)
        execute([str(cli), "demo-report", "--output", "demo.html"], workspace, env)
        assert (workspace / "demo.html").is_file() and (workspace / "demo.json").is_file()
        (workspace / "capabilities.txt").write_text("I am a customer support assistant. I answer support questions and do not disclose private account records.", encoding="utf-8")
        execute([str(cli), "profile-target", "--target-url", "https://example.invalid", "--profile-response-file", "capabilities.txt", "--output", "declared-profile.yaml", "--quiet-ui", "--no-banner"], workspace, env)
        assert (workspace / "declared-profile.yaml").is_file()
        execute([str(cli), "generate-tests", "--target-profile", "profile.yaml", "--output", "generated.yaml", "--max-tests", "4"], workspace, env)
        execute([str(python), "-I", "-m", "trustinspect.dynamic.engine", "--target-profile", "profile.yaml", "--output", "module-generated.yaml", "--max-tests", "4"], workspace, env)
        execute([str(python), "-I", "-c", "import yaml; from pathlib import Path; assert yaml.safe_load(Path('generated.yaml').read_text())['test_cases']; assert yaml.safe_load(Path('module-generated.yaml').read_text())['test_cases']"], workspace, env)
        summary.update(wheel=str(wheel.name), wheel_sha256=checked["wheel_sha256"], fresh_venv=True, console_commands=5, external_ai_requests=0)
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
        print("DISTRIBUTION_VERIFIED=" + json.dumps(summary))


if __name__ == "__main__":
    main()
