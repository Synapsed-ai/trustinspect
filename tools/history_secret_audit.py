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


def is_reviewed_digest(finding, blob_sha):
    """An exact historical digest field, not a broad path or rule exclusion."""
    commit = "89ed0bea08152c34de4c668dc5942b1e044a5675"
    line = finding.get("StartLine")
    return (finding.get("Commit") == commit and finding.get("File") == ".secrets.baseline"
            and finding.get("RuleID") == "generic-api-key" and line in (134, 142, 150)
            and finding.get("EndLine") == line
            and finding.get("Fingerprint") == f"{commit}:.secrets.baseline:generic-api-key:{line}"
            and blob_sha == "48288487972f4f2e011e9876f8aebf5c4efd1172")


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
        reviewed = []
        for finding in findings or []:
            commit, path = finding.get("Commit", ""), finding.get("File", "")
            blob = git("rev-parse", f"{commit}:{path}") if commit == "89ed0bea08152c34de4c668dc5942b1e044a5675" and path == ".secrets.baseline" else ""
            if is_reviewed_digest(finding, blob):
                reviewed.append(finding["Fingerprint"])
        summary["reviewed_findings"] = reviewed
        summary["review_reason"] = "Exact detect-secrets hashed_secret digest fields, manually inspected; these bytes are not credentials. No path-wide or detector-wide exclusions."
        summary["unreviewed_count"] = len(findings) - len(reviewed) if isinstance(findings, list) else None
        summary["status"] = "passed-reviewed" if result.returncode in (0, 1) and isinstance(findings, list) and not summary["unreviewed_count"] else "review-required"
        summary["finding_count"] = len(findings) if isinstance(findings, list) else None
        summary["findings"] = [safe_finding(f) for f in findings] if isinstance(findings, list) else []
        summary["stderr_sha256"] = hashlib.sha256(result.stderr).hexdigest()
    (out / "history-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("SECRET_AUDIT=" + json.dumps(summary), flush=True)
    return 0 if summary["status"] == "passed-reviewed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
