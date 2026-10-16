"""Scan fetched reachable Git history; persist locations, never secret values."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def safe_finding(finding):
    return {key: finding.get(key) for key in
            ("RuleID", "File", "StartLine", "EndLine", "Commit", "Fingerprint")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gitleaks", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    repo = Path(__file__).resolve().parents[1]
    def git(*command):
        return subprocess.check_output(["git", *command], cwd=repo, text=True, encoding="utf-8").strip()
    summary = {"time_utc": datetime.now(timezone.utc).isoformat(), "head": git("rev-parse", "HEAD"),
               "scope": "All history reachable from fetched refs; unreachable/deleted server objects and unprovided LFS bytes excluded",
               "shallow": git("rev-parse", "--is-shallow-repository"),
               "reachable_commits": int(git("rev-list", "--all", "--count")),
               "refs": git("for-each-ref", "--format=%(refname) %(objectname)").splitlines(),
               "tool": subprocess.check_output([args.gitleaks, "version"], text=True).strip()}
    if summary["shallow"] != "false" or not summary["reachable_commits"]:
        raise RuntimeError("Full fetched history required; refusing a shallow/empty audit")
    with tempfile.TemporaryDirectory(prefix="secret-review-") as tmp:
        report = Path(tmp) / "raw.json"
        result = subprocess.run([args.gitleaks, "git", str(repo), "--log-opts=--all --full-history",
                                 "--redact=100", "--no-banner", "--log-level=error", "--report-format=json",
                                 "--report-path", str(report)], capture_output=True, timeout=600)
        findings = json.loads(report.read_text(encoding="utf-8")) if report.is_file() else None
        summary["exit_code"] = result.returncode
        summary["status"] = "passed" if result.returncode == 0 and isinstance(findings, list) and not findings else "review-required"
        summary["finding_count"] = len(findings) if isinstance(findings, list) else None
        summary["findings"] = [safe_finding(f) for f in findings] if isinstance(findings, list) else []
        summary["stderr_sha256"] = hashlib.sha256(result.stderr).hexdigest()
    (out / "history-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("SECRET_AUDIT=" + json.dumps(summary), flush=True)
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
