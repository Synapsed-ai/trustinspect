from __future__ import annotations

from pathlib import Path
from difflib import SequenceMatcher
from typing import Any, Callable, Iterable, Optional
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from trustinspect.analyzers.heuristic import HeuristicTrustAnalyzer
from trustinspect.core.models import (
    Classification,
    EvidenceItem,
    EvidenceType,
    Observation,
    Target,
    TestCase,
)
from trustinspect.scanners.base import ScannerAdapter
from trustinspect.scanners.web_ui.output_capture_guard import is_prompt_echo, format_prompt_echo_error
from trustinspect.scanners.web_ui.robust_actions import dismiss_blocking_overlays, optional_selector, prepare_input_element, set_input_text


_TI_NULLISH_SELECTORS = {"", "none", "null", "nil", "n/a", "na", "-", "undefined"}


def _ti_is_nullish_selector(value) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in _TI_NULLISH_SELECTORS


def _ti_normalize_selector(value):
    if _ti_is_nullish_selector(value):
        return None
    return str(value).strip()

ProgressCallback = Callable[[dict[str, Any]], None]


class WebUiScanner(ScannerAdapter):
    """
    Selenium-based Web UI execution engine for TrustInspect.

    It collects prompt/response evidence from LLM Web UIs and emits optional
    progress events so the CLI can show live prompts, responses, counters, and
    classifications during the scan.
    """

    def __init__(
        self,
        input_selector: str,
        output_selector: str,
        send_selector: Optional[str] = None,
        frame_selector: Optional[str] = None,
        headless: bool = True,
        wait_time: int = 20,
        evidence_dir: str | Path = "reports/evidence",
        analyzer: Optional[HeuristicTrustAnalyzer] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        self.input_selector = input_selector
        self.output_selector = output_selector
        self.send_selector = _ti_normalize_selector(send_selector)
        self.frame_selector = _ti_normalize_selector(frame_selector)
        self.headless = headless
        self.wait_time = wait_time
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.analyzer = analyzer or HeuristicTrustAnalyzer()
        self.progress_callback = progress_callback
        self.driver = None

    def run(self, target: Target, test_cases: Iterable[TestCase]) -> list[Observation]:
        cases = list(test_cases)
        self._emit({"event": "run_started", "total": len(cases), "target": target.name, "url": target.url})
        self._open_browser(target)
        observations: list[Observation] = []
        self._target_runtime = getattr(target, 'metadata', {}) if isinstance(getattr(target, 'metadata', {}), dict) else {}
        try:
            for idx, test_case in enumerate(cases, 1):
                self._emit(
                    {
                        "event": "test_started",
                        "idx": idx,
                        "total": len(cases),
                        "remaining": len(cases) - idx + 1,
                        "test_case": {
                            "id": test_case.id,
                            "name": test_case.name,
                            "category": test_case.category,
                            "payload": test_case.payload,
                        },
                    }
                )
                observation = self._run_single(target, test_case, idx)
                observations.append(observation)
                response = self._evidence_value(observation, EvidenceType.RESPONSE)
                if not response:
                    response = self._evidence_value(observation, EvidenceType.LOG)
                self._emit(
                    {
                        "event": "test_completed",
                        "idx": idx,
                        "total": len(cases),
                        "test_id": test_case.id,
                        "classification": observation.classification.value,
                        "confidence": observation.confidence,
                        "response": response,
                        "rationale": observation.rationale,
                        "duration_seconds": observation.metadata.get("duration_seconds"),
                    }
                )
        finally:
            self.close()
            self._emit({"event": "run_completed", "total": len(cases)})
        return observations

    def _emit(self, event: dict[str, Any]) -> None:
        if self.progress_callback:
            try:
                self.progress_callback(event)
            except Exception:
                # UI callbacks must never break scanning.
                pass


    # TRUSTINSPECT_CHALLENGE_RUNTIME_PATCH
    def _trustinspect_hide_common_overlays(self):
        """Hide known cookie/floating overlays that intercept clicks in AI challenge UIs."""
        try:
            selectors = [
                '#hs-eu-cookie-settings-button',
                'button[id*="cookie" i]',
                'button[aria-label*="cookie" i]',
                '[id*="cookie" i]',
                '[class*="cookie" i]',
            ]
            script = """
            const selectors = arguments[0];
            for (const sel of selectors) {
              try {
                document.querySelectorAll(sel).forEach(el => {
                  el.style.pointerEvents = 'none';
                  el.style.display = 'none';
                  el.style.visibility = 'hidden';
                });
              } catch(e) {}
            }
            """
            self.driver.execute_script(script, selectors)
        except Exception:
            pass

    def _open_browser(self, target: Target) -> None:
        if not target.url:
            raise ValueError("Web UI scanner requires target.url")
        if _ti_is_nullish_selector(self.input_selector):
            raise ValueError("Web UI scanner requires a valid input_selector. The value cannot be empty, null or none.")
        if _ti_is_nullish_selector(self.output_selector):
            raise ValueError("Web UI scanner requires a valid output_selector. The value cannot be empty, null or none. Calibrate the target first.")

        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1440,1100")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(45)
        self.driver.get(target.url)
        dismiss_blocking_overlays(self.driver, target)

        if self.frame_selector:
            WebDriverWait(self.driver, self.wait_time).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, self.frame_selector)
            )
            frame = self.driver.find_element(By.CSS_SELECTOR, self.frame_selector)
            self.driver.switch_to.frame(frame)

    def _run_single(self, target: Target, test_case: TestCase, idx: int) -> Observation:
        assert self.driver is not None
        started = time.time()
        screenshot_path: Optional[Path] = None

        try:
            runtime = getattr(self, '_target_runtime', {}) or {}
            if runtime.get('runtime', {}).get('reload_before_each_test') or runtime.get('reload_before_each_test'):
                self.driver.get(target.url)
                dismiss_blocking_overlays(self.driver, target)
                time.sleep(0.3)

            previous_texts = self._candidate_output_texts()
            previous_count = len(previous_texts)
            previous_text = previous_texts[-1] if previous_texts else ""

            input_el = WebDriverWait(self.driver, self.wait_time).until(
                lambda d: d.find_element(By.CSS_SELECTOR, self.input_selector)
            )
            dismiss_blocking_overlays(self.driver, target)
            prepare_input_element(self.driver, input_el, wait_time=self.wait_time, target=target)
            set_input_text(self.driver, input_el, test_case.payload)

            if self.send_selector:
                send_el = self.driver.find_element(By.CSS_SELECTOR, self.send_selector)
                send_el.click()
            else:
                input_el.send_keys(Keys.ENTER)

            response_text = self._wait_for_response(previous_count, previous_text)
            _ti_payload_for_guard = getattr(test_case, 'payload', None) or getattr(test_case, 'prompt', '')
            _ti_is_echo, _ti_echo_reason, _ti_echo_score = is_prompt_echo(_ti_payload_for_guard, response_text)
            if _ti_is_echo:
                raise RuntimeError(format_prompt_echo_error(
                    _ti_payload_for_guard,
                    response_text,
                    input_selector=self.input_selector,
                    output_selector=self.output_selector,
                ))
            classification, confidence, rationale = self.analyzer.analyze(test_case, response_text)

            screenshot_path = self._save_screenshot(target, test_case, idx)
            evidence = self._build_evidence(test_case, response_text, screenshot_path)

            return Observation(
                id=f"obs-{idx}",
                target=target,
                test_case=test_case,
                classification=classification,
                confidence=confidence,
                evidence=evidence,
                analyzer=self.analyzer.ANALYZER_VERSION,
                rationale=rationale,
                metadata={
                    "scanner": "web-ui-selenium",
                    "duration_seconds": round(time.time() - started, 3),
                    "input_selector": self.input_selector,
                    "output_selector": self.output_selector,
                    "previous_output_count": previous_count,
                },
            )

        except Exception as exc:
            return self._error_observation(target, test_case, idx, started, exc)

    def _candidate_output_texts(self) -> list[str]:
        assert self.driver is not None
        texts: list[str] = []
        for el in self.driver.find_elements(By.CSS_SELECTOR, self.output_selector):
            try:
                text = el.text.strip()
            except Exception:
                text = ""
            if text:
                texts.append(text)
        return texts

    def _normalize_capture_text(self, value: str | None) -> str:
        value = value or ""
        return " ".join(value.split()).strip().lower()

    def _looks_like_prompt_echo(self, candidate: str) -> bool:
        prompt = self._normalize_capture_text(getattr(self, "_active_prompt_text", ""))
        text = self._normalize_capture_text(candidate)
        if not prompt or not text:
            return False
        if text == prompt:
            return True
        if len(prompt) >= 80 and (prompt in text or text in prompt):
            return True
        if len(prompt) >= 40 and len(text) >= 40:
            try:
                return SequenceMatcher(None, prompt, text).ratio() >= 0.92
            except Exception:
                return False
        return False

    def _wait_for_response(self, *args) -> str:
        """
        Wait for a new assistant response while rejecting user-message echoes.

        Some WebChat/BotFramework-style targets expose user and assistant bubbles
        through the same selector. In that case the last matched node can be the
        submitted prompt itself, which would create false positives. This method
        scans all matched output nodes from newest to oldest and returns the first
        new, non-empty text that is not already present before submission and does
        not look like the prompt just submitted.
        """
        assert self.driver is not None

        previous_text = ""
        if args:
            previous_text = str(args[-1] or "")
        previous_norm = self._normalize_capture_text(previous_text)
        previous_seen = {
            self._normalize_capture_text(t)
            for t in getattr(self, "_previous_output_texts", [])
            if self._normalize_capture_text(t)
        }
        if previous_norm:
            previous_seen.add(previous_norm)

        def changed(d):
            elems = d.find_elements(By.CSS_SELECTOR, self.output_selector)
            if not elems:
                return False
            texts = []
            for elem in elems:
                try:
                    value = elem.text.strip()
                except Exception:
                    value = ""
                if value:
                    texts.append(value)
            for text in reversed(texts):
                norm = self._normalize_capture_text(text)
                if not norm:
                    continue
                if norm in previous_seen:
                    continue
                if self._looks_like_prompt_echo(text):
                    continue
                return text
            return False

        response = WebDriverWait(self.driver, self.wait_time).until(changed)
        return str(response).strip()

    def _build_evidence(self, test_case: TestCase, response_text: str, screenshot_path: Optional[Path]) -> list[EvidenceItem]:
        evidence = [
            EvidenceItem(
                id=f"ev-{test_case.id}-prompt",
                evidence_type=EvidenceType.PROMPT,
                value=test_case.payload,
            ),
            EvidenceItem(
                id=f"ev-{test_case.id}-response",
                evidence_type=EvidenceType.RESPONSE,
                value=response_text,
            ),
        ]
        if screenshot_path:
            evidence.append(
                EvidenceItem(
                    id=f"ev-{test_case.id}-screenshot",
                    evidence_type=EvidenceType.SCREENSHOT,
                    value=str(screenshot_path),
                )
            )
        return evidence

    def _error_observation(self, target: Target, test_case: TestCase, idx: int, started: float, exc: Exception) -> Observation:
        screenshot_path: Optional[Path] = None
        dom_path: Optional[Path] = None
        try:
            screenshot_path = self._save_screenshot(target, test_case, idx, suffix="error")
        except Exception:
            screenshot_path = None
        try:
            dom_path = self._save_dom_snapshot(target, test_case, idx)
        except Exception:
            dom_path = None

        error_message = str(exc) or exc.__class__.__name__
        diagnostic = (
            f"Web UI execution failed for test case {test_case.id}. "
            f"Reason: {error_message}. "
            f"Input selector: {self.input_selector!r}. "
            f"Output selector: {self.output_selector!r}. "
            f"Wait time: {self.wait_time}s."
        )

        evidence = [
            EvidenceItem(
                id=f"ev-{idx}-prompt",
                evidence_type=EvidenceType.PROMPT,
                value=test_case.payload,
            ),
            EvidenceItem(
                id=f"ev-{idx}-log",
                evidence_type=EvidenceType.LOG,
                value=diagnostic,
                metadata={
                    "error_type": exc.__class__.__name__,
                    "input_selector": self.input_selector,
                    "output_selector": self.output_selector,
                    "wait_time_seconds": self.wait_time,
                },
            ),
        ]
        if screenshot_path:
            evidence.append(
                EvidenceItem(
                    id=f"ev-{idx}-screenshot",
                    evidence_type=EvidenceType.SCREENSHOT,
                    value=str(screenshot_path),
                )
            )
        if dom_path:
            evidence.append(
                EvidenceItem(
                    id=f"ev-{idx}-dom",
                    evidence_type=getattr(EvidenceType, "DOM_SNAPSHOT", EvidenceType.LOG),
                    value=str(dom_path),
                )
            )

        return Observation(
            id=f"obs-{idx}",
            target=target,
            test_case=test_case,
            classification=Classification.ERROR,
            confidence=0.0,
            evidence=evidence,
            analyzer=self.analyzer.ANALYZER_VERSION,
            rationale=diagnostic,
            metadata={
                "scanner": "web-ui-selenium",
                "duration_seconds": round(time.time() - started, 3),
                "error_type": exc.__class__.__name__,
                "input_selector": self.input_selector,
                "output_selector": self.output_selector,
            },
        )

    def _evidence_value(self, observation: Observation, evidence_type: EvidenceType) -> str:
        for item in observation.evidence:
            if item.evidence_type == evidence_type:
                return str(item.value)
        return ""

    def _save_screenshot(self, target: Target, test_case: TestCase, idx: int, suffix: str = "response") -> Path:
        assert self.driver is not None
        safe_target = "".join(c if c.isalnum() or c in "-_" else "_" for c in target.id)
        safe_case = "".join(c if c.isalnum() or c in "-_" else "_" for c in test_case.id)
        path = self.evidence_dir / f"{safe_target}_{idx:03d}_{safe_case}_{suffix}.png"
        self.driver.save_screenshot(str(path))
        return path

    def _save_dom_snapshot(self, target: Target, test_case: TestCase, idx: int) -> Path:
        assert self.driver is not None
        safe_target = "".join(c if c.isalnum() or c in "-_" else "_" for c in target.id)
        safe_case = "".join(c if c.isalnum() or c in "-_" else "_" for c in test_case.id)
        path = self.evidence_dir / f"{safe_target}_{idx:03d}_{safe_case}_dom.html"
        path.write_text(self.driver.page_source, encoding="utf-8")
        return path

    def close(self) -> None:
        if self.driver is not None:
            try:
                self.driver.quit()
            finally:
                self.driver = None

# --- TrustInspect scanner realtime progress monkeypatch ---
def _ti_obj_get(obj, *names, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        for name in names:
            if name in obj and obj.get(name) is not None:
                return obj.get(name)
        return default
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def _ti_extract_evidence_value(observation, wanted):
    wanted = wanted.lower()
    for ev in getattr(observation, "evidence", []) or []:
        et = str(getattr(ev, "evidence_type", "") or "").lower()
        value = getattr(ev, "value", None)
        if wanted in et and value is not None:
            return value
    return ""


try:
    _ti_original_run = WebUiScanner.run
    _ti_original_run_single = WebUiScanner._run_single

    def _ti_run_with_total(self, target, test_cases):
        if not isinstance(test_cases, list):
            test_cases = list(test_cases)
        self._ti_current_total = len(test_cases)
        return _ti_original_run(self, target, test_cases)

    def _ti_run_single_with_progress(self, target, test_case, idx):
        total = int(getattr(self, "_ti_current_total", 0) or 0)
        cb = getattr(self, "progress_callback", None)
        prompt = _ti_obj_get(test_case, "payload", "prompt", default="")
        test_id = _ti_obj_get(test_case, "id", "test_id", default="")
        test_name = _ti_obj_get(test_case, "name", default="")
        metadata = _ti_obj_get(test_case, "metadata", default={}) or {}
        if isinstance(test_case, dict):
            metadata = test_case.get("metadata", {}) or {}
        category = _ti_obj_get(test_case, "category", default=metadata.get("category", ""))
        layer = metadata.get("aitg_layer") or metadata.get("layer") or _ti_obj_get(test_case, "aitg_layer", default="")
        source = metadata.get("source") or _ti_obj_get(test_case, "source", default="static")
        parent = metadata.get("parent_static_test_id") or _ti_obj_get(test_case, "parent_static_test_id", default="")

        if cb:
            try:
                cb({
                    "type": "test_start",
                    "index": idx,
                    "total": total,
                    "test_id": test_id,
                    "test_name": test_name,
                    "source": source,
                    "parent_static_test_id": parent,
                    "aitg_layer": layer,
                    "category": category,
                    "prompt": prompt,
                })
            except Exception:
                pass

        observation = _ti_original_run_single(self, target, test_case, idx)

        if cb:
            try:
                response = _ti_extract_evidence_value(observation, "response")
                if not response:
                    response = _ti_extract_evidence_value(observation, "error")
                classification = getattr(getattr(observation, "classification", ""), "value", getattr(observation, "classification", ""))
                cb({
                    "type": "test_result",
                    "index": idx,
                    "total": total,
                    "test_id": test_id,
                    "test_name": test_name,
                    "source": source,
                    "parent_static_test_id": parent,
                    "aitg_layer": layer,
                    "category": category,
                    "prompt": prompt,
                    "response": response,
                    "classification": str(classification),
                    "confidence": getattr(observation, "confidence", 0.0),
                    "rationale": getattr(observation, "rationale", ""),
                })
            except Exception:
                pass
        return observation

    if not getattr(WebUiScanner, "_ti_realtime_monkeypatch", False):
        WebUiScanner.run = _ti_run_with_total
        WebUiScanner._run_single = _ti_run_single_with_progress
        WebUiScanner._ti_realtime_monkeypatch = True
except Exception:
    pass
# --- end TrustInspect scanner realtime progress monkeypatch ---

