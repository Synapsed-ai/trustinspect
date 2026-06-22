from __future__ import annotations

import json
from pathlib import Path

from trustinspect.core.models import Assessment


class EvidenceStore:
    """Simple filesystem-backed store for TrustInspect assessment evidence."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_assessment_json(self, assessment: Assessment, filename: str = "assessment.json") -> Path:
        path = self.root / filename
        path.write_text(json.dumps(assessment.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path
