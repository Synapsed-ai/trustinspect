from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from trustinspect.core.models import (
    Classification,
    EvidenceItem,
    EvidenceType,
    Observation,
    Target,
    TestCase,
)


class SynInspectEduAdapter:
    """
    Adapter for importing SynInspect EDU scanner results.

    Expected JSON format:
    [
      {
        "probe": {
          "vulnerability_id": "LLM08",
          "vulnerability_name": "Vector and Embedding Weakness",
          "category": "LLM08",
          "payload": "..."
        },
        "analysis": {
          "classification": "VULNERABILITY",
          "confidence_score": 0.95,
          "analysis_comment": "...",
          "llm_response": "..."
        }
      }
    ]

    Next implementation task:
    add `--json-output` to SynInspect EDU so TrustInspect can import
    evidence without parsing HTML.
    """

    def import_json(self, path: str | Path, target: Target) -> List[Observation]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        observations: List[Observation] = []

        for idx, row in enumerate(data, 1):
            probe = row.get("probe", {})
            analysis = row.get("analysis", {})

            test_case = TestCase(
                id=probe.get("vulnerability_id") or f"syninspect-{idx}",
                name=probe.get("vulnerability_name") or "SynInspect EDU Test",
                category=probe.get("category") or "Uncategorized",
                objective=probe.get("objective") or "Execute SynInspect EDU probe and observe target behavior.",
                payload=probe.get("payload") or "",
                mappings={"OWASP LLM": [probe.get("vulnerability_id", "Unmapped")]},
            )

            classification = self._parse_classification(analysis.get("classification"))

            evidence = [
                EvidenceItem(
                    id=f"ev-{idx}-prompt",
                    evidence_type=EvidenceType.PROMPT,
                    value=test_case.payload,
                ),
                EvidenceItem(
                    id=f"ev-{idx}-response",
                    evidence_type=EvidenceType.RESPONSE,
                    value=analysis.get("llm_response", ""),
                    metadata={"analysis_comment": analysis.get("analysis_comment", "")},
                ),
            ]

            observations.append(
                Observation(
                    id=f"obs-{idx}",
                    target=target,
                    test_case=test_case,
                    classification=classification,
                    confidence=float(analysis.get("confidence_score") or 0.0),
                    evidence=evidence,
                    analyzer=analysis.get("analyzer", "SynInspect EDU"),
                    rationale=analysis.get("analysis_comment", ""),
                    metadata={"source": "syninspect-edu"},
                )
            )

        return observations

    def _parse_classification(self, value: Any) -> Classification:
        value = (value or "").upper()
        if value == Classification.VULNERABILITY.value:
            return Classification.VULNERABILITY
        if value == Classification.SAFE.value:
            return Classification.SAFE
        if value == Classification.ERROR.value:
            return Classification.ERROR
        return Classification.POSSIBLE
