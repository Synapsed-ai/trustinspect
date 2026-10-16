"""Never publish matched values, snippets or personal commit fields in audit artifacts."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("history_scan", Path(__file__).resolve().parents[1] / "tools/history_secret_audit.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_artifact_schema_excludes_secret_and_snippet():
    raw = {"RuleID": "example", "File": "fixture.txt", "StartLine": 1, "EndLine": 1,
           "Commit": "a" * 40, "Fingerprint": "location-id", "Secret": "SYNTHETIC-PRIVATE", "Match": "SYNTHETIC-PRIVATE",
           "Message": "private commit message", "Email": "author@example.test", "Author": "someone"}
    safe = module.safe_finding(raw)
    assert set(safe) == {"RuleID", "File", "StartLine", "EndLine", "Commit", "Fingerprint"}
    assert "SYNTHETIC-PRIVATE" not in str(safe)
