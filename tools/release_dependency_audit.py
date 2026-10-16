"""Build from Git, freeze/audit complete environments, and replay hashed installs.

No publish, git write, credential access, automatic fix or ignored advisory.
Outputs are review evidence for one commit/platform, not a release approval.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
import tarfile
import tempfile
import unicodedata
import venv
from datetime import datetime, timezone
try:
    import tomllib
except ImportError:  # Python 3.10 controller only
    import tomli as tomllib

AUDITOR = "pip-audit==2.10.1"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def pins_from_report(report):
    """Freeze every resolved direct/transitive dependency, not just roots."""
    records = []
    seen = set()
    for item in report["install"]:
        meta = item["metadata"]
        name = canonical(meta["name"])
        if name == "trustinspect":
            continue  # local project is verified separately, not a PyPI lookup
        version = meta["version"]
        digest = item["download_info"]["archive_info"]["hashes"]["sha256"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) or name in seen:
            raise ValueError("Invalid or duplicate dependency name")
        if not re.fullmatch(r"[A-Za-z0-9.!+_-]+", version) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid dependency version or SHA-256")
        seen.add(name)
        records.append({"name": name, "version": version, "sha256": digest,
                        "direct": bool(item.get("requested")),
                        "requires_dist": meta.get("requires_dist", []),
                        "license_expression": meta.get("license_expression"),
                        "license": meta.get("license"),
                        "license_classifiers": [c for c in meta.get("classifier", []) if c.startswith("License ::")],
                        "project_urls": meta.get("project_url", [])})
    if not records:
        raise ValueError("Empty dependency resolution is not an audit")
    return sorted(records, key=lambda r: r["name"])


def extract_tracked_archive(archive, dest):
    names = set()
    with tarfile.open(archive) as tar:
        for member in tar:
            path = PurePosixPath(member.name)
            normalized = unicodedata.normalize("NFC", member.name).casefold()
            if path.is_absolute() or ".." in path.parts or "\\" in member.name or normalized in names:
                raise ValueError("Unsafe or normalization-colliding archive member")
            names.add(normalized)
            target = dest.joinpath(*path.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                source = tar.extractfile(member)
                assert source is not None
                target.write_bytes(source.read())
                target.chmod(member.mode & 0o777)
            else:
                raise ValueError("Links and special files are not accepted in release source")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tests", action="store_true")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    repo = Path(__file__).resolve().parents[1]
    summary = {"status": "incomplete", "time_utc": datetime.now(timezone.utc).isoformat(),
               "python": platform.python_version(), "platform": platform.platform(),
               "machine": platform.machine(), "auditor": AUDITOR, "audits": {}, "tests_requested": args.tests}
    env = {k: v for k, v in os.environ.items() if k not in {
        "PYTHONPATH", "PYTHONHOME", "PIP_EXTRA_INDEX_URL", "PIP_INDEX_URL", "PIP_TRUSTED_HOST"}}
    env.update(PIP_INDEX_URL="https://pypi.org/simple", PIP_DISABLE_PIP_VERSION_CHECK="1",
               PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONNOUSERSITE="1")

    def run(command, name, cwd=repo, allow_failure=False, extra_env=None):
        result = subprocess.run([str(c) for c in command], cwd=cwd, env=env | (extra_env or {}),
                                text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=900)
        (out / (name + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
        print(f"STEP {name}: exit={result.returncode}", flush=True)
        if result.returncode and not allow_failure:
            raise RuntimeError(f"{name} failed; inspect retained log")
        return result

    def newenv(path):
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(path)
        py = path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        # Python <=3.11 may bootstrap an old setuptools unrelated to the project.
        # Remove it only from this newly created disposable venv. Builders and
        # test environments subsequently install the declared secure minimum.
        run([py, "-m", "pip", "uninstall", "-y", "setuptools"], path.name + "-bootstrap-clean")
        return py

    def freeze(py, name):
        result = run([py, "-m", "pip", "list", "--format=json"], name + "-packages")
        packages = sorted(json.loads(result.stdout), key=lambda p: canonical(p["name"]))
        text = "".join(f'{p["name"]}=={p["version"]}\n' for p in packages if canonical(p["name"]) != "trustinspect")
        (out / (name + ".txt")).write_text(text, encoding="utf-8")
        return out / (name + ".txt")

    try:
        summary["commit"] = run(["git", "rev-parse", "HEAD"], "commit").stdout.strip()
        summary["tree"] = run(["git", "rev-parse", "HEAD^{tree}"], "tree").stdout.strip()
        with tempfile.TemporaryDirectory(prefix="trustinspect-release-") as temp:
            temp = Path(temp)
            source = temp / "source"
            source.mkdir()
            archive = temp / "tracked.tar"
            with archive.open("wb") as stream:
                subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=repo, stdout=stream, check=True)
            extract_tracked_archive(archive, source)
            metadata = tomllib.loads((source / "pyproject.toml").read_text(encoding="utf-8"))
            summary["declared_runtime"] = metadata["project"]["dependencies"]
            summary["declared_build"] = metadata["build-system"]["requires"]
            minima = {}
            for req in [*summary["declared_runtime"], *summary["declared_build"],
                        *metadata["project"]["optional-dependencies"]["dev"],
                        *metadata["project"]["optional-dependencies"]["packaging"]]:
                match = re.fullmatch(r"([A-Za-z0-9_.-]+)>=([0-9A-Za-z.]+)", req)
                if not match:
                    raise ValueError("Minimum-version audit needs an explicit lower bound")
                minima[canonical(match[1])] = match[2]
            (out / "declared-minima.txt").write_text("".join(f"{k}=={v}\n" for k, v in sorted(minima.items())), encoding="utf-8")
            builder = newenv(temp / "builder")
            run([builder, "-m", "pip", "install", "--upgrade", "pip", *summary["declared_build"],
                 *metadata["project"]["optional-dependencies"]["packaging"]], "build-tool-install")
            toolpins = freeze(builder, "build-environment")
            dist = out / "dist"
            dist.mkdir()
            run([builder, "-m", "build", "--no-isolation", "--sdist", "--outdir", dist, source], "sdist-build")
            sdist, = dist.glob("*.tar.gz")
            run([builder, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "--wheel-dir", dist, sdist], "wheel-from-sdist")
            wheel, = dist.glob("*.whl")
            run([builder, "-m", "twine", "check", sdist, wheel], "metadata-check")
            summary["artifacts"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (sdist, wheel)}
            runtime = newenv(temp / "runtime")
            run([runtime, "-m", "pip", "install", "--upgrade", "pip"], "runtime-pip-install")
            run([runtime, "-m", "pip", "install", "--report", out / "install-report.json", wheel], "runtime-install")
            report = read_json(out / "install-report.json")
            records = pins_from_report(report)
            direct_names = {canonical(re.match(r"[A-Za-z0-9_.-]+", req).group()) for req in summary["declared_runtime"]}
            for record in records:
                record["direct"] = record["name"] in direct_names
            (out / "dependency-graph.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
            pins = out / "runtime-pins.txt"
            pins.write_text("".join(f'{r["name"]}=={r["version"]}\n' for r in records), encoding="utf-8")
            hashes = out / "runtime-hashed.txt"
            hashes.write_text("".join(f'{r["name"]}=={r["version"]} --hash=sha256:{r["sha256"]}\n' for r in records), encoding="utf-8")
            summary["dependencies"] = [{k: r[k] for k in ("name", "version", "direct")} for r in records]
            runtime_environment = freeze(runtime, "runtime-environment")
            run([runtime, "-m", "pip", "inspect"], "pip-inspect")
            auditor = newenv(temp / "auditor")
            run([auditor, "-m", "pip", "install", AUDITOR], "auditor-install")
            freeze(auditor, "auditor-environment")
            for scope, requirements in (("runtime", pins), ("runtime-environment", runtime_environment), ("build", toolpins), ("declared-minima", out / "declared-minima.txt")):
                audit = out / f"audit-{scope}.json"
                res = run([auditor, "-m", "pip_audit", "--strict", "--no-deps", "--disable-pip", "--progress-spinner", "off",
                           "-r", requirements, "--format", "json", "--output", audit], f"audit-{scope}", allow_failure=True)
                summary["audits"][scope] = {"exit_code": res.returncode}
                if audit.exists():
                    data = read_json(audit)
                    deps = data["dependencies"] if isinstance(data, dict) else data
                    summary["audits"][scope].update(packages=len(deps),
                        vulnerabilities=sum(len(d.get("vulns", [])) for d in deps),
                        skipped=[d["name"] for d in deps if d.get("skip_reason")])
            sbom_result = run([auditor, "-m", "pip_audit", "--strict", "--no-deps", "--disable-pip", "--progress-spinner", "off",
                 "-r", pins, "--format", "cyclonedx-json", "--output", out / "runtime-sbom.json"], "runtime-sbom", allow_failure=True)
            summary["sbom_exit_code"] = sbom_result.returncode
            replay = newenv(temp / "replay")
            run([replay, "-m", "pip", "install", "--upgrade", "pip"], "replay-pip-install")
            run([replay, "-m", "pip", "install", "--require-hashes", "--only-binary=:all:", "-r", hashes], "hashed-reinstall")
            run([replay, "-m", "pip", "install", "--no-deps", wheel], "replay-wheel-install")
            run([replay, "-m", "pip", "check"], "replay-pip-check")
            spec = importlib.util.spec_from_file_location("release_probe", source / "scripts/maintenance/verify_installed_distribution.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            checked = module.inspect_wheel(wheel, source)
            expected = temp / "expected.json"
            expected.write_text(json.dumps(checked["hashes"]), encoding="utf-8")
            probe = temp / "probe.py"
            probe.write_text(module.PROBE, encoding="utf-8")
            workspace = temp / "outside-checkout"
            workspace.mkdir()
            run([replay, "-I", "-B", "-X", "utf8", probe, expected], "installed-probe", cwd=workspace)
            summary["hashed_reinstall_and_probe"] = "passed"
            if args.tests:
                run([replay, "-m", "pip", "install", "-c", pins, *metadata["project"]["optional-dependencies"]["dev"]], "test-tool-install")
                testpins = freeze(replay, "test-environment")
                run([replay, "-m", "pytest", "-q", "--junitxml=" + str(out / "unit-tests.xml")], "unit-tests", cwd=repo)
                run([replay, "-m", "pytest", "-q", "-s", "tests/browser", "--junitxml=" + str(out / "browser-tests.xml")],
                    "browser-tests", cwd=repo, extra_env={"TRUSTINSPECT_BROWSER_TESTS": "1", "TI_BROWSER_EVIDENCE_DIR": str(out / "browser")})
                summary["tests"] = "passed"
                res = run([auditor, "-m", "pip_audit", "--strict", "--no-deps", "--disable-pip", "--progress-spinner", "off",
                           "-r", testpins, "--format", "json", "--output", out / "audit-tests.json"], "audit-tests", allow_failure=True)
                summary["audits"]["tests"] = {"exit_code": res.returncode}
                if (out / "audit-tests.json").exists():
                    deps = read_json(out / "audit-tests.json")["dependencies"]
                    summary["audits"]["tests"].update(packages=len(deps),
                        vulnerabilities=sum(len(d.get("vulns", [])) for d in deps),
                        skipped=[d["name"] for d in deps if d.get("skip_reason")])
            summary["status"] = "passed" if all(a["exit_code"] == 0 and a.get("packages", 0) > 0 and not a.get("skipped") for a in summary["audits"].values()) and summary["sbom_exit_code"] == 0 else "audit-findings-or-error"
    except Exception as exc:
        summary["status"] = "error"
        summary["error"] = str(exc)
    finally:
        (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("RELEASE_AUDIT=" + json.dumps(summary), flush=True)
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
