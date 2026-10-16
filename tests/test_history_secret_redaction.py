"""Never publish matches; accept reviewed findings only at exact immutable locations."""
import importlib.util
from pathlib import Path
import pytest

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


def known():
    commit = "89ed0bea08152c34de4c668dc5942b1e044a5675"
    return {"RuleID": "generic-api-key", "File": ".secrets.baseline", "Commit": commit,
            "StartLine": 134, "EndLine": 134, "Fingerprint": f"{commit}:.secrets.baseline:generic-api-key:134"}


def test_only_exact_inspected_digest_is_reviewed():
    assert module.is_reviewed_digest(known(), "48288487972f4f2e011e9876f8aebf5c4efd1172")
    assert not module.is_reviewed_digest(known(), "0" * 40)


@pytest.mark.parametrize("field,value", [("File", "credentials.txt"), ("Commit", "0" * 40), ("StartLine", 133),
                                         ("EndLine", 135), ("RuleID", "private-key"), ("Fingerprint", "different")])
def test_new_locations_and_rules_still_require_review(field, value):
    finding = known()
    finding[field] = value
    assert not module.is_reviewed_digest(finding, "48288487972f4f2e011e9876f8aebf5c4efd1172")
