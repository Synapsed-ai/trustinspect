from __future__ import annotations

from collections import Counter
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from trustinspect.core.models import Assessment, Classification

try:
    from trustinspect.reporting.suite_metadata import enrich_assessment_suite_metadata
except Exception:  # pragma: no cover
    def enrich_assessment_suite_metadata(assessment: Any) -> Any:
        return assessment

try:
    from trustinspect.core.versions import (
        TRUSTINSPECT_VERSION,
        SCANNER_ENGINE_VERSION,
        ANALYZER_ENGINE_VERSION,
        DYNAMIC_ENGINE_VERSION,
        TARGET_PROFILER_VERSION,
        REPORT_SCHEMA_VERSION,
    )
except Exception:  # pragma: no cover - defensive fallback for old installs
    TRUSTINSPECT_VERSION = "v0.3-alpha"
    SCANNER_ENGINE_VERSION = "web-ui-selenium v0.3"
    ANALYZER_ENGINE_VERSION = "heuristic-evidence v0.5"
    DYNAMIC_ENGINE_VERSION = "per-static-deterministic-template v0.3"
    TARGET_PROFILER_VERSION = "capability-profile v0.2"
    REPORT_SCHEMA_VERSION = "html-report v0.6"


CLASSIFICATION_ORDER = {
    "VULNERABILITY": 0,
    "POSSIBLE VULNERABILITY": 1,
    "POSSIBLE": 1,
    "ERROR": 2,
    "SAFE": 3,
}

LAYER_ORDER = {
    "AI Application Testing": 0,
    "AI Model Testing": 1,
    "AI Infrastructure Testing": 2,
    "AI Data Testing": 3,
    "OWASP LLM Top 10": 4,
    "Other": 9,
}

OFFICIAL_AITG_LAYERS = [
    "AI Application Testing",
    "AI Model Testing",
    "AI Infrastructure Testing",
    "AI Data Testing",
]


class HtmlReporter:
    """Generates an evidence-oriented TrustInspect HTML report."""

    def __init__(self) -> None:
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, assessment: Assessment, output: str | Path) -> Path:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)

        assessment = enrich_assessment_suite_metadata(assessment)
        report = self._build_report_context(assessment)
        template = self.env.get_template("assessment_report.html.j2")
        html = template.render(assessment=assessment, report=report, summary=report["summary"])
        output.write_text(html, encoding="utf-8")
        return output

    def _build_report_context(self, assessment: Assessment) -> Dict[str, Any]:
        metadata = _to_plain(getattr(assessment, "metadata", {}) or {})
        observations = list(getattr(assessment, "observations", []) or [])
        findings = list(getattr(assessment, "findings", []) or [])

        summary = self._summary(assessment)
        started_human = _format_datetime(getattr(assessment, "started_at", None))
        completed_human = _format_datetime(getattr(assessment, "completed_at", None))
        duration_human = metadata.get("duration_human") or _duration_human(
            getattr(assessment, "started_at", None), getattr(assessment, "completed_at", None)
        )

        observation_rows = self._observation_rows(observations)
        finding_rows = self._finding_rows(findings)
        aitg_coverage = self._aitg_coverage(observation_rows)
        aitg_visual = self._aitg_visual_summary(aitg_coverage, finding_rows)
        generated_plan = self._generated_plan(metadata)
        generated_plan_summary = self._generated_plan_summary(generated_plan)
        target_profile = _target_profile(metadata)
        scanner_status = self._scanner_status(summary)

        suite_info = _suite_info(metadata, observation_rows, generated_plan)
        metadata_with_suite = dict(metadata)
        metadata_with_suite.setdefault("suite_id", suite_info["suite_id"])
        metadata_with_suite.setdefault("suite_name", suite_info["suite_name"])
        metadata_with_suite.setdefault("suite_display_name", suite_info["suite_name"])
        metadata_with_suite.setdefault("suite_version", suite_info["suite_version"])
        engine_versions = _engine_versions(metadata_with_suite)

        suite_name = suite_info["suite_name"]
        suite_id = suite_info["suite_id"]
        suite_version = suite_info["suite_version"]

        report = {
            "summary": summary,
            "metadata": metadata,
            "target_profile": target_profile,
            "generated_plan": generated_plan,
            "generated_plan_summary": generated_plan_summary,
            "observation_rows": observation_rows,
            "finding_rows": finding_rows,
            "aitg_coverage": aitg_coverage,
            "aitg_visual": aitg_visual,
            "engine_versions": engine_versions,
            "started_human": started_human,
            "completed_human": completed_human,
            "duration_human": duration_human,
            "scanner_status": scanner_status,
            "assessment_mode": metadata.get("assessment_mode") or _infer_assessment_mode(summary),
            "generation_strategy": metadata.get("generation_strategy") or "-",
            "suite_id": suite_id,
            "suite_name": suite_name,
            "suite_version": suite_version,
            "is_aitg": _is_aitg_observations(observation_rows) or str(suite_id).startswith("owasp-aitg"),
            "target_profile_path": metadata.get("target_profile_path") or metadata.get("profile_path") or metadata.get("target_profile_file") or "-",
            "generated_tests_path": metadata.get("generated_tests_path") or metadata.get("generated_tests_file") or metadata.get("generated_tests") or "-",
        }
        return report

    def _summary(self, assessment: Assessment) -> Dict[str, int]:
        counts: Dict[str, int] = {
            "vulnerabilities": 0,
            "possible": 0,
            "safe": 0,
            "errors": 0,
            "total": len(getattr(assessment, "observations", []) or []),
            "static": 0,
            "dynamic": 0,
        }
        for obs in getattr(assessment, "observations", []) or []:
            cls = _classification_value(getattr(obs, "classification", None))
            if cls == "VULNERABILITY":
                counts["vulnerabilities"] += 1
            elif cls == "SAFE":
                counts["safe"] += 1
            elif cls == "ERROR":
                counts["errors"] += 1
            else:
                counts["possible"] += 1

            source = _source_value(getattr(getattr(obs, "test_case", None), "metadata", {}) or {})
            if source == "dynamic":
                counts["dynamic"] += 1
            else:
                counts["static"] += 1

        counts["effective_tests"] = counts["total"] - counts["errors"]
        return counts

    def _observation_rows(self, observations: List[Any]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for idx, obs in enumerate(observations, start=1):
            tc = getattr(obs, "test_case", None)
            tc_meta = _to_plain(getattr(tc, "metadata", {}) or {})
            cls = _classification_value(getattr(obs, "classification", None))
            test_id = str(getattr(tc, "id", "-"))
            layer = _layer_for_test(test_id, tc_meta)
            row = {
                "execution_index": idx,
                "test_id": test_id,
                "test_name": getattr(tc, "name", "-"),
                "category": getattr(tc, "category", "-"),
                "aitg_layer": layer,
                "layer": layer,
                "classification": cls,
                "classification_css": _classification_css(cls),
                "confidence": _float(getattr(obs, "confidence", 0.0)),
                "rationale": getattr(obs, "rationale", "") or "-",
                "source": _source_value(tc_meta).upper(),
                "parent_static_test_id": tc_meta.get("parent_static_test_id") or tc_meta.get("parent_id") or tc_meta.get("parent") or "-",
                "execution_time": _to_plain(getattr(obs, "metadata", {}) or {}).get("execution_time_seconds")
                or _to_plain(getattr(obs, "metadata", {}) or {}).get("execution_time")
                or "-",
                "evidence": _evidence_rows(getattr(obs, "evidence", []) or []),
            }
            rows.append(row)

        rows.sort(
            key=lambda r: (
                CLASSIFICATION_ORDER.get(r["classification"], 1),
                LAYER_ORDER.get(r["layer"], 9),
                r.get("test_id", ""),
                r["execution_index"],
            )
        )
        return rows

    def _finding_rows(self, findings: List[Any]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for finding in findings:
            meta = _to_plain(getattr(finding, "metadata", {}) or {})
            mappings = _to_plain(getattr(finding, "mappings", {}) or {})
            source_test = meta.get("source_test") or meta.get("source_test_id") or meta.get("test_id") or "-"
            if source_test == "-":
                source_test = _extract_source_test(getattr(finding, "id", "")) or "-"
            row = {
                "id": getattr(finding, "id", "-"),
                "title": getattr(finding, "title", "-"),
                "source_test": source_test,
                "source_layer": _layer_for_test(str(source_test), meta),
                "severity": _enum_value(getattr(finding, "severity", "-")),
                "confidence": _float(getattr(finding, "confidence", 0.0)),
                "evidence": _evidence_rows(getattr(finding, "evidence", []) or []),
                "mappings": mappings,
            }
            rows.append(row)
        rows.sort(key=lambda r: (_severity_order(r["severity"]), r["source_layer"], -r["confidence"], r["source_test"]))
        return rows

    def _aitg_coverage(self, observation_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        layers: Dict[str, Dict[str, Any]] = {
            "AI Application Testing": {"total": 0, "findings": 0, "errors": 0, "safe": 0, "possible": 0},
            "AI Model Testing": {"total": 0, "findings": 0, "errors": 0, "safe": 0, "possible": 0},
            "AI Infrastructure Testing": {"total": 0, "findings": 0, "errors": 0, "safe": 0, "possible": 0},
            "AI Data Testing": {"total": 0, "findings": 0, "errors": 0, "safe": 0, "possible": 0},
            "OWASP LLM Top 10": {"total": 0, "findings": 0, "errors": 0, "safe": 0, "possible": 0},
            "Other": {"total": 0, "findings": 0, "errors": 0, "safe": 0, "possible": 0},
        }
        test_status: Dict[str, Dict[str, Any]] = {}
        for row in observation_rows:
            layer = row.get("layer") or "Other"
            if layer not in layers:
                layer = "Other"
            layers[layer]["total"] += 1
            cls = row["classification"]
            if cls == "VULNERABILITY":
                layers[layer]["findings"] += 1
            elif cls == "ERROR":
                layers[layer]["errors"] += 1
            elif cls == "SAFE":
                layers[layer]["safe"] += 1
            else:
                layers[layer]["possible"] += 1

            base_id = _base_test_id(row["test_id"])
            current = test_status.setdefault(base_id, {"layer": layer, "static": "-", "dynamic": "-", "result": "SAFE", "findings": 0, "errors": 0})
            if row["source"] == "DYNAMIC":
                current["dynamic"] = _merge_status(current.get("dynamic", "-"), cls)
            else:
                current["static"] = _merge_status(current.get("static", "-"), cls)
            current["result"] = _merge_status(current.get("result", "SAFE"), cls)
            if cls == "VULNERABILITY":
                current["findings"] += 1
            if cls == "ERROR":
                current["errors"] += 1

        ordered_tests = [
            {"test_id": k, **v}
            for k, v in sorted(test_status.items(), key=lambda item: (LAYER_ORDER.get(item[1]["layer"], 9), item[0]))
        ]
        return {"layers": layers, "tests": ordered_tests}

    def _aitg_visual_summary(self, coverage: Mapping[str, Any], finding_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        layers = coverage.get("layers", {}) if isinstance(coverage, dict) else {}
        rows: List[Dict[str, Any]] = []
        for layer in OFFICIAL_AITG_LAYERS:
            counts = layers.get(layer, {}) or {}
            total = int(counts.get("total", 0) or 0)
            findings = int(counts.get("findings", 0) or 0)
            possible = int(counts.get("possible", 0) or 0)
            safe = int(counts.get("safe", 0) or 0)
            errors = int(counts.get("errors", 0) or 0)
            rows.append(
                {
                    "layer": layer,
                    "short": layer.replace("AI ", "").replace(" Testing", ""),
                    "total": total,
                    "findings": findings,
                    "possible": possible,
                    "safe": safe,
                    "errors": errors,
                    "findings_pct": _pct(findings, total),
                    "possible_pct": _pct(possible, total),
                    "safe_pct": _pct(safe, total),
                    "errors_pct": _pct(errors, total),
                }
            )
        severity = Counter(row.get("severity", "-") for row in finding_rows)
        impacted_layers = Counter(row.get("source_layer", "Other") for row in finding_rows)
        return {
            "layers": rows,
            "severity": severity.most_common(),
            "impacted_layers": [(k, v) for k, v in impacted_layers.most_common() if k in OFFICIAL_AITG_LAYERS],
            "total_findings": len(finding_rows),
        }

    def _generated_plan(self, metadata: Mapping[str, Any]) -> List[Dict[str, Any]]:
        plan = metadata.get("generated_test_plan") or metadata.get("generated_tests_plan") or metadata.get("dynamic_test_plan") or []
        if not isinstance(plan, list):
            return []
        normalized = []
        for item in plan:
            row = _to_plain(item)
            if not isinstance(row, dict):
                continue
            parent = row.get("parent_static_test_id") or row.get("parent") or row.get("parent_id") or "-"
            normalized.append(
                {
                    "id": row.get("id") or row.get("test_id") or "-",
                    "name": row.get("name") or "-",
                    "parent_static_test_id": parent,
                    "aitg_layer": _layer_for_test(str(parent), {}),
                    "reason": row.get("generation_reason") or row.get("reason") or row.get("selection_reason") or "-",
                }
            )
        return normalized

    def _generated_plan_summary(self, generated_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        layers = Counter(row.get("aitg_layer") or "Other" for row in generated_plan)
        parents = Counter(row.get("parent_static_test_id") or "-" for row in generated_plan)
        return {
            "count": len(generated_plan),
            "by_aitg_layer": [(layer, count) for layer, count in layers.most_common() if layer in OFFICIAL_AITG_LAYERS or layer == "OWASP LLM Top 10"],
            "parents_count": len([p for p in parents if p != "-"]),
        }

    def _scanner_status(self, summary: Mapping[str, int]) -> Dict[str, Any]:
        total = int(summary.get("total", 0) or 0)
        errors = int(summary.get("errors", 0) or 0)
        if total == 0:
            return {"level": "info", "message": "No tests were executed."}
        if errors == total:
            return {
                "level": "critical",
                "message": "All tests ended in ERROR. This report does not evaluate model behavior and indicates a setup, selector, or execution issue.",
            }
        ratio = errors / total
        if ratio >= 0.30:
            return {
                "level": "warning",
                "message": f"{errors} test(s) could not be evaluated. Review error evidence before drawing conclusions.",
            }
        if errors > 0:
            return {
                "level": "notice",
                "message": f"{errors} test(s) could not be evaluated. Findings are based only on effective tests.",
            }
        return {"level": "ok", "message": "All tests completed without scanner/runtime errors."}


def _to_plain(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "value") and not isinstance(value, (str, int, float, bool)):
        try:
            return value.value
        except Exception:
            pass
    if is_dataclass(value):
        return {k: _to_plain(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _to_plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    return value


def _enum_value(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value or "-")


def _classification_value(value: Any) -> str:
    text = _enum_value(value).upper()
    if text == "POSSIBLE":
        return "POSSIBLE VULNERABILITY"
    return text


def _classification_css(value: str) -> str:
    if value == "VULNERABILITY":
        return "vuln"
    if value == "SAFE":
        return "safe"
    if value == "ERROR":
        return "error"
    return "possible"


def _source_value(metadata: Mapping[str, Any]) -> str:
    source = str(metadata.get("source") or metadata.get("origin") or "static").lower()
    if source in {"dynamic", "adaptive"}:
        return "dynamic"
    return "static"


def _float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _format_datetime(value: Any) -> str:
    dt = _parse_datetime(value)
    if not dt:
        return str(value or "-")
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except Exception:
            try:
                dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
            except Exception:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _duration_human(started: Any, completed: Any) -> str:
    start_dt = _parse_datetime(started)
    end_dt = _parse_datetime(completed)
    if not start_dt or not end_dt:
        return "-"
    seconds = max(0, int((end_dt - start_dt).total_seconds()))
    if seconds < 60:
        return f"{seconds}s"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {sec}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {sec}s"




def _suite_info(metadata: Mapping[str, Any], observation_rows: Iterable[Mapping[str, Any]], generated_plan: Iterable[Mapping[str, Any]]) -> Dict[str, str]:
    """Return a stable suite id/name/version even when the CLI did not pass suite metadata.

    The report must be self-explanatory. Older scan paths only passed the test cases path,
    so we infer the suite from test IDs as a fallback.
    """
    raw_id = (
        metadata.get("suite_id")
        or metadata.get("suite")
        or metadata.get("static_suite")
        or metadata.get("suite_slug")
        or metadata.get("test_suite")
        or ""
    )
    raw_name = metadata.get("suite_display_name") or metadata.get("suite_name") or metadata.get("suite_label") or ""
    raw_version = metadata.get("suite_version") or ""

    ids = []
    for row in observation_rows or []:
        tid = str(row.get("test_id") or "")
        if tid:
            ids.append(tid)
    for row in generated_plan or []:
        tid = str(row.get("id") or row.get("parent_static_test_id") or "")
        if tid:
            ids.append(tid)

    joined = " ".join(ids).upper()
    normalized_raw_id = str(raw_id or "").strip().lower().replace("_", "-")

    mapping = {
        "trustinspect-baseline": ("trustinspect-baseline", "TrustInspect Baseline", "v0.3"),
        "owasp-llm-top10-2025-light": ("owasp-llm-top10-2025-light", "OWASP LLM Top 10 2025 — Light", "v0.1-light"),
        "owasp-llm-top10-2025-full": ("owasp-llm-top10-2025-full", "OWASP LLM Top 10 2025 — Full", "v0.1-full"),
        "owasp-aitg-light": ("owasp-aitg-light", "OWASP AI Testing Guide — Light", "v0.1-light"),
        "owasp-aitg-full": ("owasp-aitg-full", "OWASP AI Testing Guide — Full", "v0.1-full"),
    }

    if normalized_raw_id in mapping:
        sid, sname, sversion = mapping[normalized_raw_id]
    elif "AITG-" in joined:
        # The light suite has exactly one base check per official AITG ID. Full uses variants.
        if "-V" in joined or "FULL" in joined:
            sid, sname, sversion = mapping["owasp-aitg-full"]
        else:
            sid, sname, sversion = mapping["owasp-aitg-light"]
    elif "OWASP-LLM" in joined:
        if "FULL" in joined:
            sid, sname, sversion = mapping["owasp-llm-top10-2025-full"]
        else:
            sid, sname, sversion = mapping["owasp-llm-top10-2025-light"]
    elif "TI-BASE" in joined or "TRUSTINSPECT" in joined:
        sid, sname, sversion = mapping["trustinspect-baseline"]
    else:
        sid = str(raw_id or "-") or "-"
        sname = str(raw_name or raw_id or "-") or "-"
        sversion = str(raw_version or "-") or "-"

    if raw_name:
        sname = str(raw_name)
    if raw_version:
        sversion = str(raw_version)

    return {"suite_id": sid, "suite_name": sname, "suite_version": sversion}

def _engine_versions(metadata: Mapping[str, Any]) -> Dict[str, str]:
    versions = metadata.get("engine_versions") if isinstance(metadata, dict) else None
    if not isinstance(versions, dict):
        versions = {}
    suite_label = metadata.get("suite_display_name") or metadata.get("suite_name") or metadata.get("suite_id") or versions.get("suite") or "-"
    suite_version = metadata.get("suite_version") or "-"
    if suite_label != "-" and suite_version != "-":
        suite_label = f"{suite_label} {suite_version}"
    return {
        "TrustInspect": str(versions.get("trustinspect") or metadata.get("trustinspect_version") or TRUSTINSPECT_VERSION),
        "Scanner": str(versions.get("scanner") or metadata.get("scanner_version") or SCANNER_ENGINE_VERSION),
        "Analyzer": str(versions.get("analyzer") or metadata.get("analyzer_version") or ANALYZER_ENGINE_VERSION),
        "Dynamic Engine": str(versions.get("dynamic_engine") or metadata.get("dynamic_engine_version") or DYNAMIC_ENGINE_VERSION),
        "Target Profiler": str(versions.get("target_profiler") or metadata.get("target_profiler_version") or TARGET_PROFILER_VERSION),
        "Report Schema": str(versions.get("report_schema") or metadata.get("report_schema_version") or REPORT_SCHEMA_VERSION),
        "Suite": str(suite_label),
    }


def _target_profile(metadata: Mapping[str, Any]) -> Dict[str, Any]:
    profile = metadata.get("target_profile") or metadata.get("profile") or {}
    profile = _to_plain(profile)
    return profile if isinstance(profile, dict) else {}


def _evidence_rows(evidence: Iterable[Any]) -> List[Dict[str, str]]:
    rows = []
    for ev in evidence:
        ev_type = _enum_value(getattr(ev, "evidence_type", "evidence"))
        rows.append({"type": ev_type, "value": str(getattr(ev, "value", ""))})
    return rows


def _layer_for_test(test_id: str, metadata: Mapping[str, Any]) -> str:
    layer = metadata.get("aitg_layer") or metadata.get("layer")
    if layer:
        return str(layer)
    test_id = str(test_id or "")
    if "AITG-APP" in test_id:
        return "AI Application Testing"
    if "AITG-MOD" in test_id:
        return "AI Model Testing"
    if "AITG-INF" in test_id:
        return "AI Infrastructure Testing"
    if "AITG-DAT" in test_id:
        return "AI Data Testing"
    if "OWASP-LLM" in test_id or test_id.startswith("LLM"):
        return "OWASP LLM Top 10"
    return "Other"


def _is_aitg_observations(rows: Iterable[Mapping[str, Any]]) -> bool:
    return any(str(row.get("test_id", "")).startswith("AITG-") for row in rows)


def _base_test_id(test_id: str) -> str:
    text = str(test_id or "")
    if "-DYN-" in text:
        return text.split("-DYN-")[0]
    if "-VAR-" in text:
        return text.split("-VAR-")[0]
    return text


def _merge_status(current: str, new: str) -> str:
    order = {"VULNERABILITY": 4, "POSSIBLE VULNERABILITY": 3, "ERROR": 2, "SAFE": 1, "-": 0}
    return new if order.get(new, 0) > order.get(current, 0) else current


def _severity_order(severity: str) -> int:
    return {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}.get(str(severity).upper(), 5)


def _extract_source_test(finding_id: str) -> Optional[str]:
    text = str(finding_id or "")
    if text.startswith("TI-"):
        text = text[3:]
    parts = text.split("-")
    if len(parts) >= 3 and parts[0] in {"AITG", "OWASP"}:
        return "-".join(parts[:3]) if parts[0] == "AITG" else "-".join(parts[:4])
    if "AITG-" in str(finding_id):
        idx = str(finding_id).find("AITG-")
        candidate = str(finding_id)[idx:].split("-001")[0]
        return candidate
    return None


def _infer_assessment_mode(summary: Mapping[str, int]) -> str:
    return "adaptive" if summary.get("dynamic", 0) else "static"


def _pct(value: int, total: int) -> int:
    if not total:
        return 0
    return int(round((value / total) * 100))
