from __future__ import annotations

"""Dynamic test generation tied to a static test suite.

This module implements the TrustInspect adaptive semantics:

    static tests are loaded from a user-selected catalog/suite and are executed all;
    dynamic tests are contextual variants generated *per static test* using the
    Target Capability Profile.

Example:
    10 static OWASP Top 10 LLM light tests + --dynamic-tests-per-static 1
    => 10 dynamic variants + 10 static tests = 20 total.

The implementation is deterministic/template-based. No LLM is used for test generation.
"""

from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
import re

from trustinspect.core.models import TestCase
from trustinspect.dynamic.risk_mapper import normalize_target_profile
from trustinspect.dynamic.template_engine import load_dynamic_templates, render_template


RISK_ORDER = [
    "prompt_manipulation",
    "sensitive_data_exposure",
    "system_instruction_disclosure",
    "hidden_instruction_following",
    "unsafe_output_echo",
    "unauthorized_action_request",
    "domain_boundary_escape",
    "resource_exhaustion",
]


CATEGORY_TO_RISK_AREAS: dict[str, list[str]] = {
    # OWASP LLM Top 10 2025
    "llm01": ["prompt_manipulation", "domain_boundary_escape"],
    "prompt injection": ["prompt_manipulation", "domain_boundary_escape"],
    "prompt manipulation": ["prompt_manipulation", "domain_boundary_escape"],
    "llm02": ["sensitive_data_exposure"],
    "sensitive": ["sensitive_data_exposure"],
    "privacy": ["sensitive_data_exposure"],
    "llm03": ["system_instruction_disclosure", "sensitive_data_exposure"],
    "supply chain": ["system_instruction_disclosure"],
    "llm04": ["hidden_instruction_following"],
    "poisoning": ["hidden_instruction_following"],
    "data / model": ["hidden_instruction_following"],
    "llm05": ["unsafe_output_echo"],
    "output": ["unsafe_output_echo"],
    "xss": ["unsafe_output_echo"],
    "llm06": ["unauthorized_action_request"],
    "agency": ["unauthorized_action_request"],
    "agentic": ["unauthorized_action_request"],
    "llm07": ["system_instruction_disclosure"],
    "system prompt": ["system_instruction_disclosure"],
    "system instruction": ["system_instruction_disclosure"],
    "llm08": ["hidden_instruction_following"],
    "vector": ["hidden_instruction_following"],
    "embedding": ["hidden_instruction_following"],
    "rag": ["hidden_instruction_following"],
    "context": ["hidden_instruction_following"],
    "llm09": ["domain_boundary_escape", "prompt_manipulation"],
    "misinformation": ["domain_boundary_escape"],
    "bias": ["domain_boundary_escape"],
    "safety": ["domain_boundary_escape"],
    "llm10": ["resource_exhaustion"],
    "unbounded": ["resource_exhaustion"],
    "resource": ["resource_exhaustion"],
    "reliability": ["resource_exhaustion"],
}


RISK_ALIASES: dict[str, str] = {
    "prompt_injection": "prompt_manipulation",
    "jailbreak": "prompt_manipulation",
    "sensitive_information_disclosure": "sensitive_data_exposure",
    "sensitive_data_leak": "sensitive_data_exposure",
    "data_leak": "sensitive_data_exposure",
    "system_prompt_leakage": "system_instruction_disclosure",
    "prompt_leakage": "system_instruction_disclosure",
    "context_manipulation": "hidden_instruction_following",
    "indirect_prompt_injection": "hidden_instruction_following",
    "vector_embedding_weakness": "hidden_instruction_following",
    "excessive_agency": "unauthorized_action_request",
    "improper_output_handling": "unsafe_output_echo",
    "unbounded_consumption": "resource_exhaustion",
}


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {}


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _metadata(test_case: Any) -> dict[str, Any]:
    meta = _field(test_case, "metadata", {}) or {}
    return dict(meta) if isinstance(meta, dict) else {}


def _normalize_risk(value: str | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    return RISK_ALIASES.get(raw, raw)


def infer_static_test_risk_areas(test_case: Any) -> list[str]:
    """Infer relevant dynamic risk areas for a static test case.

    The function uses explicit metadata first, then category/name/id/prompt keyword matching.
    It intentionally returns a *ranked list* so multiple dynamic variants can be generated
    per static test if requested.
    """
    meta = _metadata(test_case)
    explicit_values: list[str] = []
    for key in ("risk_area", "selected_risk_area", "owasp_risk", "risk", "trustinspect_risk_area"):
        val = meta.get(key) or _field(test_case, key, None)
        if isinstance(val, str):
            explicit_values.append(val)
        elif isinstance(val, list):
            explicit_values.extend([str(v) for v in val])

    inferred: list[str] = []
    for value in explicit_values:
        normalized = _normalize_risk(value)
        if normalized and normalized not in inferred:
            inferred.append(normalized)

    text = " ".join(
        str(x or "")
        for x in (
            _field(test_case, "id", ""),
            _field(test_case, "name", ""),
            _field(test_case, "category", ""),
            _field(test_case, "objective", ""),
            _field(test_case, "payload", ""),
            _field(test_case, "prompt", ""),
        )
    ).lower()

    # Strong OWASP category overrides. These avoid generic keywords such as
    # "output" causing LLM10 / unbounded-consumption tests to generate
    # unsafe-output-echo variants. For dynamic-per-static generation, the
    # parent static test category should dominate generic keyword matches.
    if any(marker in text for marker in ["llm10", "unbounded consumption", "unbounded output", "resource exhaustion", "resource use"]):
        return ["resource_exhaustion"]
    if any(marker in text for marker in ["llm05", "improper output", "unsafe output echo", "xss echo"]):
        return ["unsafe_output_echo"]
    if any(marker in text for marker in ["llm06", "excessive agency", "unauthorized action", "agency"]):
        return ["unauthorized_action_request"]
    if any(marker in text for marker in ["llm07", "system prompt leakage", "system instruction disclosure"]):
        return ["system_instruction_disclosure"]
    if any(marker in text for marker in ["llm08", "vector and embedding", "embedding weakness", "hidden instruction", "rag"]):
        return ["hidden_instruction_following"]


    # LLM10 / unbounded-consumption tests must map to resource_exhaustion only.
    # Do not generate unsafe-output-echo variants for resource-consumption tests.
    if any(marker in text for marker in ["llm10", "unbounded", "resource", "repeat the string", "trustinspect_data"]):
        return ["resource_exhaustion"]

    for keyword, risk_list in CATEGORY_TO_RISK_AREAS.items():
        if keyword in text:
            for risk in risk_list:
                if risk not in inferred:
                    inferred.append(risk)

    if not inferred:
        inferred.append("prompt_manipulation")

    # Stable priority ordering while preserving useful inferred alternatives.
    ordered = [risk for risk in RISK_ORDER if risk in inferred]
    ordered.extend([risk for risk in inferred if risk not in ordered])
    return ordered


def _template_risk(template: dict[str, Any]) -> str:
    return str(template.get("risk_area") or "prompt_manipulation")


def _template_applies_to_risk(template: dict[str, Any], risk_area: str) -> bool:
    if _template_risk(template) == risk_area:
        return True
    applies = template.get("applies_to") or {}
    risk_areas = applies.get("risk_areas") or []
    return risk_area in risk_areas or "any" in risk_areas


def select_templates_for_static_test(
    static_test: Any,
    templates: Sequence[dict[str, Any]],
    dynamic_tests_per_static: int,
) -> list[dict[str, Any]]:
    if dynamic_tests_per_static <= 0:
        return []

    risk_areas = infer_static_test_risk_areas(static_test)
    selected: list[dict[str, Any]] = []

    for risk in risk_areas:
        candidates = [t for t in templates if _template_applies_to_risk(t, risk)]
        candidates = sorted(candidates, key=lambda t: int(t.get("priority", 50)))
        for template in candidates:
            if template not in selected:
                selected.append(template)
            if len(selected) >= dynamic_tests_per_static:
                return selected

    # Fallback: fill with highest-priority templates if the risk-specific pool is small.
    for template in sorted(templates, key=lambda t: int(t.get("priority", 50))):
        if template not in selected:
            selected.append(template)
        if len(selected) >= dynamic_tests_per_static:
            break

    return selected


def _safe_test_id(value: str) -> str:
    value = (value or "STATIC").strip()
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value)
    return value.strip("-") or "STATIC"


def _to_test_case(data: dict[str, Any]) -> TestCase:
    return TestCase(
        id=str(data.get("id") or data.get("test_id") or "TI-DYN-000"),
        name=str(data.get("name") or "Dynamic TrustInspect Test"),
        category=str(data.get("category") or "Trustworthy AI / Dynamic"),
        objective=str(data.get("objective") or data.get("expected_behavior") or "Execute dynamic TrustInspect test case."),
        payload=str(data.get("payload") or data.get("prompt") or ""),
        expected_behavior=data.get("expected_behavior"),
        failure_indicators=list(data.get("failure_indicators") or []),
        mappings=dict(data.get("mappings") or {}),
        metadata=dict(data.get("metadata") or {}),
    )


def generate_dynamic_tests_for_static_suite(
    static_tests: Sequence[Any],
    target_profile: Any,
    dynamic_tests_per_static: int = 0,
    max_dynamic_tests: Optional[int] = None,
    template_dir: str | Path = "examples/dynamic_templates",
    return_dicts: bool = False,
) -> list[TestCase] | list[dict[str, Any]]:
    """Generate contextual variants for each static test.

    Args:
        static_tests: Loaded static/base test cases. These are never modified.
        target_profile: TargetCapabilityProfile or dict.
        dynamic_tests_per_static: Number of dynamic variants to generate per static test.
        max_dynamic_tests: Optional global cap, useful for large static suites.
        template_dir: Dynamic template directory.
        return_dicts: If True, return serializable dicts; otherwise TestCase objects.
    """
    if dynamic_tests_per_static <= 0 or not static_tests:
        return []

    profile = normalize_target_profile(_as_dict(target_profile))
    templates = load_dynamic_templates(template_dir)
    generated: list[dict[str, Any]] = []

    for static_index, static_test in enumerate(static_tests, start=1):
        chosen_templates = select_templates_for_static_test(
            static_test=static_test,
            templates=templates,
            dynamic_tests_per_static=dynamic_tests_per_static,
        )
        parent_id = str(_field(static_test, "id", f"STATIC-{static_index:03d}"))
        parent_name = str(_field(static_test, "name", "Static TrustInspect Test"))
        parent_category = str(_field(static_test, "category", "Uncategorized"))
        parent_meta = _metadata(static_test)
        parent_risks = infer_static_test_risk_areas(static_test)

        for variant_index, template in enumerate(chosen_templates, start=1):
            rendered = render_template(template, profile, index=len(generated) + 1)
            rendered_id = f"{_safe_test_id(parent_id)}-DYN-{variant_index:03d}"
            template_name = str(rendered.get("name") or template.get("name") or "Dynamic Variant")
            rendered["id"] = rendered_id
            rendered["name"] = f"{template_name} — dynamic variant of {parent_id}"
            rendered["source"] = "dynamic"
            rendered["parent_static_test_id"] = parent_id
            rendered["parent_static_test_name"] = parent_name
            rendered["parent_static_test_category"] = parent_category
            rendered["dynamic_variant_index"] = variant_index

            meta = dict(rendered.get("metadata") or {})
            meta.update(
                {
                    "source": "dynamic",
                    "test_origin": "dynamic",
                    "parent_static_test_id": parent_id,
                    "parent_static_test_name": parent_name,
                    "parent_static_test_category": parent_category,
                    "parent_static_risk_areas": parent_risks,
                    "dynamic_variant_index": variant_index,
                    "dynamic_tests_per_static": dynamic_tests_per_static,
                    "template_id": meta.get("template_id") or template.get("template_id"),
                    "generation_strategy": "per-static-deterministic-template",
                }
            )
            base_reason = meta.get("generation_reason") or "Generated from static test metadata and target profile."
            meta["generation_reason"] = (
                f"Generated as dynamic variant {variant_index}/{dynamic_tests_per_static} for static test "
                f"{parent_id} ({parent_name}) using target profile domain "
                f"'{profile.get('inferred_domain', 'generic')}' and template risk area "
                f"'{rendered.get('risk_area', meta.get('risk_area', 'contextual_risk'))}'. {base_reason}"
            )
            rendered["metadata"] = meta
            generated.append(rendered)

            if max_dynamic_tests is not None and max_dynamic_tests > 0 and len(generated) >= max_dynamic_tests:
                if return_dicts:
                    return generated
                return [_to_test_case(item) for item in generated]

    if return_dicts:
        return generated
    return [_to_test_case(item) for item in generated]
