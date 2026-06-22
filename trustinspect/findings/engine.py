from __future__ import annotations

from trustinspect.core.models import Classification, Finding, Observation, Severity


class FindingEngine:
    """Converts scanner observations into TrustInspect findings."""

    def generate_from_observation(self, observation: Observation) -> Finding | None:
        if observation.classification != Classification.VULNERABILITY:
            return None

        dimension = self._map_dimension(observation.test_case.category)
        severity = self._severity_from_category(observation.test_case.category)

        return Finding(
            id=self._finding_id(observation),
            title=f"{observation.test_case.name}",
            severity=severity,
            confidence=observation.confidence,
            trustworthiness_dimension=dimension,
            observation_id=observation.id,
            description=(
                "The target system exhibited behavior that matched the failure "
                "indicators for this Trustworthy AI test case."
            ),
            impact=(
                "The observed behavior may reduce the trustworthiness of the AI "
                "application and should be reviewed by engineering, testing, and "
                "assurance stakeholders."
            ),
            remediation=(
                "Review the system prompt, instruction hierarchy, input handling, "
                "retrieved-context isolation, tool-call authorization, and response "
                "filtering. Re-run the same test case after mitigation."
            ),
            evidence=observation.evidence,
            mappings=observation.test_case.mappings,
            metadata={
                "source_observation_classification": observation.classification.value,
                "source_test_id": observation.test_case.id,
                "test_origin": observation.test_case.metadata.get("test_origin") or observation.test_case.metadata.get("generator") or "unknown",
            },
        )

    def _finding_id(self, observation: Observation) -> str:
        """Build a clean finding id without duplicated TI- prefixes.

        Previous versions produced values such as TI-TI-BASE-004-001. We keep the
        source test id visible but avoid duplicating the project prefix.
        """
        base = (observation.test_case.id or "CASE").strip().replace(" ", "-")
        if base.upper().startswith("TI-"):
            return f"{base}-001"
        return f"TI-{base}-001"

    def _map_dimension(self, category: str) -> str:
        c = (category or "").lower()
        if "sensitive" in c or "privacy" in c:
            return "Privacy"
        if "agency" in c or "tool" in c or "agent" in c or "authorization" in c:
            return "Human Oversight / Safety"
        if "rag" in c or "embedding" in c or "prompt" in c or "context" in c:
            return "Robustness"
        if "misinformation" in c or "unsafe" in c:
            return "Safety"
        if "resource" in c or "reliability" in c:
            return "Reliability"
        return "Security / Robustness"

    def _severity_from_category(self, category: str) -> Severity:
        c = (category or "").lower()
        if "sensitive" in c or "agency" in c or "tool" in c or "authorization" in c:
            return Severity.HIGH
        if "prompt" in c or "embedding" in c or "rag" in c or "context" in c:
            return Severity.MEDIUM
        return Severity.MEDIUM
