from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


STATUS_ORDER = {
    "VULNERABILITY": 0,
    "POSSIBLE VULNERABILITY": 1,
    "POSSIBLE": 1,
    "ERROR": 2,
    "SAFE": 3,
}

AITG_LAYER_BY_PREFIX = {
    "AITG-APP": "AI Application Testing",
    "AITG-MOD": "AI Model Testing",
    "AITG-INF": "AI Infrastructure Testing",
    "AITG-DAT": "AI Data Testing",
}

AITG_LAYER_ORDER = [
    "AI Application Testing",
    "AI Model Testing",
    "AI Infrastructure Testing",
    "AI Data Testing",
]

AITG_LAYER_SHORT = {
    "AI Application Testing": "APP",
    "AI Model Testing": "MOD",
    "AI Infrastructure Testing": "INF",
    "AI Data Testing": "DAT",
}


def enum_value(value: Any) -> str:
    return str(getattr(value, "value", value) or "")


def get_metadata(obj: Any) -> Dict[str, Any]:
    meta = getattr(obj, "metadata", None)
    return meta if isinstance(meta, dict) else {}


def get_test_case(obs: Any) -> Any:
    return getattr(obs, "test_case", None)


def get_test_id_from_tc(tc: Any) -> str:
    if tc is None:
        return "-"
    return str(getattr(tc, "id", None) or get_metadata(tc).get("id") or "-")


def get_test_name_from_tc(tc: Any) -> str:
    if tc is None:
        return "-"
    return str(getattr(tc, "name", None) or get_metadata(tc).get("name") or "-")


def get_category_from_tc(tc: Any) -> str:
    if tc is None:
        return "-"
    return str(getattr(tc, "category", None) or get_metadata(tc).get("category") or "-")


def get_payload_from_tc(tc: Any) -> str:
    if tc is None:
        return ""
    return str(getattr(tc, "payload", None) or getattr(tc, "prompt", None) or get_metadata(tc).get("prompt") or "")


def get_classification(obs: Any) -> str:
    return enum_value(getattr(obs, "classification", "")) or "UNKNOWN"


def get_confidence(obs: Any) -> float:
    try:
        return float(getattr(obs, "confidence", 0.0) or 0.0)
    except Exception:
        return 0.0


def get_evidence(obs_or_finding: Any) -> List[Any]:
    ev = getattr(obs_or_finding, "evidence", [])
    return ev if isinstance(ev, list) else []


def evidence_type(ev: Any) -> str:
    return enum_value(getattr(ev, "evidence_type", "")) or "evidence"


def evidence_value(ev: Any) -> Any:
    return getattr(ev, "value", "")


def test_id_base(test_id: str) -> str:
    if "-DYN-" in test_id:
        return test_id.split("-DYN-", 1)[0]
    return test_id


def aitg_layer_from_id(test_id: str, fallback: str = "Other") -> str:
    base = test_id_base(test_id)
    for prefix, layer in AITG_LAYER_BY_PREFIX.items():
        if base.startswith(prefix):
            return layer
    return fallback


def is_aitg_test(test_id: str) -> bool:
    return test_id.startswith("AITG-") or "AITG-" in test_id


def is_owasp_llm_test(test_id: str) -> bool:
    return test_id.startswith("OWASP-LLM") or test_id.startswith("LLM")


def is_dynamic_test(tc: Any) -> bool:
    test_id = get_test_id_from_tc(tc)
    source = str(get_metadata(tc).get("source", "")).lower()
    return source in {"dynamic", "adaptive"} or "-DYN-" in test_id


def get_parent_static_test(tc: Any) -> str:
    meta = get_metadata(tc)
    parent = meta.get("parent_static_test_id") or meta.get("parent_id") or meta.get("parent")
    if parent:
        return str(parent)
    test_id = get_test_id_from_tc(tc)
    if "-DYN-" in test_id:
        return test_id.split("-DYN-", 1)[0]
    return "-"


def test_source(tc: Any) -> str:
    return "DYNAMIC" if is_dynamic_test(tc) else "STATIC"


def parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text or text.upper() == "N/A":
        return None
    # tolerate previous human format and Python isoformat
    for candidate in (text, text.replace(" UTC", "+00:00")):
        try:
            if candidate.endswith("Z"):
                candidate = candidate[:-1] + "+00:00"
            return datetime.fromisoformat(candidate)
        except Exception:
            pass
    for fmt in ("%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return None


def format_human_dt(value: Any) -> str:
    dt = parse_dt(value)
    if not dt:
        return str(value or "-")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def human_duration(started: Any, completed: Any) -> str:
    start = parse_dt(started)
    end = parse_dt(completed)
    if not start or not end:
        return "-"
    seconds = int(max(0, (end - start).total_seconds()))
    if seconds < 60:
        return f"{seconds}s"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {sec}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {sec}s"


def execution_time(obs: Any) -> str:
    meta = get_metadata(obs)
    val = (
        meta.get("execution_time")
        or meta.get("execution_time_seconds")
        or meta.get("duration")
        or meta.get("duration_seconds")
        or meta.get("elapsed")
    )
    if val is None:
        return "n/a"
    try:
        return f"{float(val):.3f}s"
    except Exception:
        return str(val)


def summarize(assessment: Any) -> Dict[str, int]:
    obs = list(getattr(assessment, "observations", []) or [])
    counts = {
        "total": len(obs),
        "vulnerabilities": 0,
        "possible": 0,
        "safe": 0,
        "errors": 0,
        "static": 0,
        "dynamic": 0,
    }
    for o in obs:
        cls = get_classification(o)
        tc = get_test_case(o)
        if cls == "VULNERABILITY":
            counts["vulnerabilities"] += 1
        elif cls == "SAFE":
            counts["safe"] += 1
        elif cls == "ERROR":
            counts["errors"] += 1
        else:
            counts["possible"] += 1
        if is_dynamic_test(tc):
            counts["dynamic"] += 1
        else:
            counts["static"] += 1
    counts["effective_tests"] = counts["total"] - counts["errors"]
    return counts


def infer_suite_id(assessment: Any) -> str:
    meta = get_metadata(assessment)
    for key in ("suite_id", "suite", "suite_name", "static_suite"):
        if meta.get(key):
            return str(meta[key])
    ids = [get_test_id_from_tc(get_test_case(o)) for o in getattr(assessment, "observations", []) or []]
    joined = " ".join(ids)
    if "AITG-" in joined:
        # If we ever introduce variant IDs we can infer full here.
        if len({test_id_base(i) for i in ids if "AITG-" in i}) >= 32:
            return "owasp-aitg-light"
        return "owasp-aitg"
    if "OWASP-LLM" in joined:
        if "FULL" in joined:
            return "owasp-llm-top10-2025-full"
        if "LIGHT" in joined:
            return "owasp-llm-top10-2025-light"
        return "owasp-llm-top10-2025"
    if any(i.startswith("TI-BASE") for i in ids):
        return "trustinspect-baseline"
    return "-"


def suite_label(suite_id: str) -> str:
    labels = {
        "owasp-aitg-light": "OWASP AI Testing Guide — Light",
        "owasp-aitg-full": "OWASP AI Testing Guide — Full",
        "owasp-aitg": "OWASP AI Testing Guide",
        "owasp-llm-top10-2025-light": "OWASP LLM Top 10 2025 — Light",
        "owasp-llm-top10-2025-full": "OWASP LLM Top 10 2025 — Full",
        "owasp-llm-top10-2025": "OWASP LLM Top 10 2025",
        "trustinspect-baseline": "TrustInspect Baseline",
    }
    return labels.get(str(suite_id), str(suite_id or "-"))


def suite_version(suite_id: str) -> str:
    if "aitg-light" in suite_id:
        return "v0.1-light"
    if "aitg-full" in suite_id:
        return "v0.1-full"
    if "llm-top10" in suite_id:
        return "2025"
    if suite_id == "trustinspect-baseline":
        return "v0.3"
    return "-"


def engine_versions(assessment: Any, suite_id: str) -> Dict[str, str]:
    meta = get_metadata(assessment)
    engines = dict(meta.get("engine_versions") or {})
    defaults = {
        "TrustInspect": "v0.3-alpha",
        "Scanner": "web-ui-selenium v0.3",
        "Analyzer": "heuristic-evidence v0.5",
        "Dynamic Engine": "per-static-deterministic-template v0.3",
        "Target Profiler": "capability-profile v0.2",
        "Report Schema": "html-report v0.6",
        "Suite": f"{suite_label(suite_id)} {suite_version(suite_id)}" if suite_id != "-" else "-",
    }
    defaults.update({k: v for k, v in engines.items() if v})
    return defaults


def profile_context(assessment: Any) -> Optional[Dict[str, Any]]:
    meta = get_metadata(assessment)
    profile = meta.get("target_profile") or meta.get("profile")
    if isinstance(profile, dict):
        return profile
    return None


def obs_view(obs: Any, index: int) -> Dict[str, Any]:
    tc = get_test_case(obs)
    test_id = get_test_id_from_tc(tc)
    cls = get_classification(obs)
    source = test_source(tc)
    layer = aitg_layer_from_id(test_id, fallback=get_category_from_tc(tc))
    evidence = get_evidence(obs)
    return {
        "index": index,
        "id": getattr(obs, "id", f"obs-{index}"),
        "test_id": test_id,
        "test_name": get_test_name_from_tc(tc),
        "test_label": f"{test_id} — {get_test_name_from_tc(tc)}",
        "category": get_category_from_tc(tc),
        "layer": layer,
        "source": source,
        "parent": get_parent_static_test(tc),
        "classification": cls,
        "confidence": get_confidence(obs),
        "rationale": getattr(obs, "rationale", "") or "-",
        "execution_time": execution_time(obs),
        "evidence": [{"type": evidence_type(ev), "value": evidence_value(ev)} for ev in evidence],
        "prompt": next((str(evidence_value(ev)) for ev in evidence if evidence_type(ev) == "prompt"), get_payload_from_tc(tc)),
        "response": next((str(evidence_value(ev)) for ev in evidence if evidence_type(ev) == "response"), ""),
    }


def sorted_observations(assessment: Any) -> List[Dict[str, Any]]:
    views = [obs_view(obs, i) for i, obs in enumerate(getattr(assessment, "observations", []) or [], start=1)]
    def sort_key(v: Dict[str, Any]):
        return (STATUS_ORDER.get(v["classification"], 1), AITG_LAYER_ORDER.index(v["layer"]) if v["layer"] in AITG_LAYER_ORDER else 99, v["test_id"])
    return sorted(views, key=sort_key)


def coverage_matrix(observations: List[Dict[str, Any]], is_aitg: bool) -> List[Dict[str, Any]]:
    if is_aitg:
        layers = AITG_LAYER_ORDER
    else:
        layers = sorted({v["layer"] for v in observations}) or ["All Tests"]
    rows = []
    for layer in layers:
        subset = [v for v in observations if v["layer"] == layer]
        if not subset and is_aitg:
            rows.append({"layer": layer, "total": 0, "findings": 0, "possible": 0, "safe": 0, "errors": 0, "pct": {}})
            continue
        total = len(subset)
        findings = sum(1 for v in subset if v["classification"] == "VULNERABILITY")
        possible = sum(1 for v in subset if v["classification"] not in {"VULNERABILITY", "SAFE", "ERROR"})
        safe = sum(1 for v in subset if v["classification"] == "SAFE")
        errors = sum(1 for v in subset if v["classification"] == "ERROR")
        def pct(n: int) -> int:
            return int(round((n / total) * 100)) if total else 0
        rows.append({
            "layer": layer,
            "short": AITG_LAYER_SHORT.get(layer, layer),
            "total": total,
            "findings": findings,
            "possible": possible,
            "safe": safe,
            "errors": errors,
            "pct": {"findings": pct(findings), "possible": pct(possible), "safe": pct(safe), "errors": pct(errors)},
        })
    return rows


def coverage_by_test(observations: List[Dict[str, Any]], is_aitg: bool) -> List[Dict[str, Any]]:
    if not is_aitg:
        return []
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for v in observations:
        groups[test_id_base(v["test_id"])].append(v)
    rows = []
    for tid in sorted(groups):
        subset = groups[tid]
        static = next((v for v in subset if v["source"] == "STATIC"), None)
        dynamic = [v for v in subset if v["source"] == "DYNAMIC"]
        findings = sum(1 for v in subset if v["classification"] == "VULNERABILITY")
        errors = sum(1 for v in subset if v["classification"] == "ERROR")
        status_values = [v["classification"] for v in subset]
        if "VULNERABILITY" in status_values:
            overall = "VULNERABILITY"
        elif any(s not in {"SAFE", "ERROR"} for s in status_values):
            overall = "POSSIBLE VULNERABILITY"
        elif errors:
            overall = "ERROR"
        else:
            overall = "SAFE"
        rows.append({
            "test_id": tid,
            "layer": aitg_layer_from_id(tid),
            "static": static["classification"] if static else "-",
            "dynamic": ", ".join(sorted({v["classification"] for v in dynamic})) if dynamic else "-",
            "overall": overall,
            "findings": findings,
            "errors": errors,
        })
    return rows


def generated_plan(assessment: Any, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    meta = get_metadata(assessment)
    raw = meta.get("generated_test_plan") or []
    plan: List[Dict[str, Any]] = []
    if isinstance(raw, list) and raw:
        for item in raw:
            if not isinstance(item, dict):
                continue
            tid = str(item.get("id") or item.get("test_id") or item.get("name") or "-")
            parent = str(item.get("parent_static_test_id") or item.get("parent") or (tid.split("-DYN-", 1)[0] if "-DYN-" in tid else "-"))
            plan.append({
                "id": tid,
                "name": str(item.get("name") or tid),
                "parent": parent,
                "layer": aitg_layer_from_id(parent if parent != "-" else tid, fallback=str(item.get("layer") or item.get("category") or "-")),
                "reason": str(item.get("reason") or item.get("generation_reason") or item.get("selection_reason") or "-"),
            })
    else:
        for v in observations:
            if v["source"] != "DYNAMIC":
                continue
            plan.append({
                "id": v["test_id"],
                "name": v["test_name"],
                "parent": v["parent"],
                "layer": v["layer"],
                "reason": "Generated as deterministic contextual variant from the parent static test and target capability profile.",
            })
    return plan


def generated_plan_summary(plan: List[Dict[str, Any]], is_aitg: bool) -> List[Dict[str, Any]]:
    if is_aitg:
        counts = Counter(item.get("layer") or "Other" for item in plan)
        rows = []
        for layer in AITG_LAYER_ORDER:
            rows.append({"label": layer, "count": counts.get(layer, 0)})
        return rows
    counts = Counter(item.get("layer") or "Other" for item in plan)
    return [{"label": k, "count": v} for k, v in counts.most_common()]


def build_report_context(assessment: Any) -> Dict[str, Any]:
    summary = summarize(assessment)
    suite_id = infer_suite_id(assessment)
    observations = sorted_observations(assessment)
    is_aitg = suite_id.startswith("owasp-aitg") or any(is_aitg_test(v["test_id"]) for v in observations)
    plan = generated_plan(assessment, observations)
    profile = profile_context(assessment)
    return {
        "summary": summary,
        "suite_id": suite_id,
        "suite_label": suite_label(suite_id),
        "suite_version": suite_version(suite_id),
        "is_aitg": is_aitg,
        "assessment_mode": get_metadata(assessment).get("assessment_mode") or get_metadata(assessment).get("mode") or ("adaptive" if summary["dynamic"] else "static"),
        "generation_strategy": get_metadata(assessment).get("generation_strategy") or ("per-static-deterministic-template" if summary["dynamic"] else "-"),
        "started_human": format_human_dt(getattr(assessment, "started_at", "")),
        "completed_human": format_human_dt(getattr(assessment, "completed_at", "")),
        "duration_human": human_duration(getattr(assessment, "started_at", None), getattr(assessment, "completed_at", None)),
        "engine_versions": engine_versions(assessment, suite_id),
        "profile": profile,
        "observations": observations,
        "coverage": coverage_matrix(observations, is_aitg),
        "coverage_by_test": coverage_by_test(observations, is_aitg),
        "generated_plan": plan,
        "generated_plan_summary": generated_plan_summary(plan, is_aitg),
    }
