from __future__ import annotations

from dataclasses import replace
from typing import Any, Optional, Tuple

try:
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Confirm, Prompt
    from rich import box
except Exception:  # pragma: no cover
    Panel = None  # type: ignore
    Table = None  # type: ignore
    Confirm = None  # type: ignore
    Prompt = None  # type: ignore
    box = None  # type: ignore

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from trustinspect.targets.registry import (
    TargetDefinition,
    normalize_optional_selector,
    save_local_target,
)

try:
    from trustinspect.scanners.web_ui.auto_selector import AutoSelector
except Exception:  # pragma: no cover
    AutoSelector = None  # type: ignore


CALIBRATION_SENTINEL = "TRUSTINSPECT_TARGET_CHECK"


def _prompt(label: str, default: Optional[str] = None) -> str:
    if Prompt:
        return Prompt.ask(label, default=default or "")
    value = input(f"{label}{f' [{default}]' if default else ''}: ").strip()
    return value or (default or "")


def _confirm(label: str, default: bool = False) -> bool:
    if Confirm:
        return Confirm.ask(label, default=default)
    suffix = "Y/n" if default else "y/N"
    value = input(f"{label} [{suffix}]: ").strip().lower()
    if not value:
        return default
    return value.startswith("y")


def _print(console: Any, message: Any, style: Optional[str] = None) -> None:
    if console:
        console.print(message, style=style)
    else:
        print(message)


def _open_driver(url: str, headless: bool = False) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1100")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(45)
    driver.get(url)
    return driver


def _selector_value(value: Any) -> Optional[str]:
    return normalize_optional_selector(value)


def _short(value: str, limit: int = 160) -> str:
    value = " ".join((value or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def _css_escape(value: str) -> str:
    return value.replace(" ", "\\ ").replace(":", "\\:").replace(".", "\\.").replace("#", "\\#")


def _build_css_selector(el: Any, max_depth: int = 5) -> str:
    parts: list[str] = []
    current = el
    depth = 0
    while current is not None and depth < max_depth:
        try:
            tag = (current.tag_name or "div").lower()
            if tag == "html":
                break
            el_id = current.get_attribute("id") or ""
            if el_id:
                parts.append(f"#{_css_escape(el_id)}")
                break
            classes = [c for c in (current.get_attribute("class") or "").split() if c]
            stable = []
            for c in classes:
                lc = c.lower()
                if any(h in lc for h in ["chat", "message", "bubble", "assistant", "bot", "response", "answer", "result", "output", "text", "webchat"]):
                    stable.append(c)
                if len(stable) >= 2:
                    break
            if not stable:
                stable = [c for c in classes if len(c) > 4][:1]
            part = tag + "".join(f".{_css_escape(c)}" for c in stable)
            parts.append(part)
            current = current.find_element(By.XPATH, "..")
            depth += 1
        except Exception:
            break
    parts.reverse()
    return " > ".join(parts) or "body"


def _switch_to_frame(driver: webdriver.Chrome, frame_selector: Optional[str], wait_time: int = 10) -> None:
    driver.switch_to.default_content()
    if frame_selector:
        WebDriverWait(driver, wait_time).until(lambda d: d.find_elements(By.CSS_SELECTOR, frame_selector))
        frame = driver.find_element(By.CSS_SELECTOR, frame_selector)
        driver.switch_to.frame(frame)


def _validate_selectors(
    driver: webdriver.Chrome,
    input_selector: Optional[str],
    output_selector: Optional[str],
    frame_selector: Optional[str],
    wait_time: int = 10,
) -> Tuple[bool, str, str]:
    try:
        _switch_to_frame(driver, frame_selector, wait_time=wait_time)
    except Exception as exc:
        return False, f"Frame selector not found or not usable: {frame_selector!r}. Error: {exc}", ""

    input_count = 0
    output_count = 0
    sample_text = ""
    if input_selector:
        try:
            input_count = len(driver.find_elements(By.CSS_SELECTOR, input_selector))
        except Exception as exc:
            return False, f"Input selector is invalid: {input_selector!r}. Error: {exc}", ""
    if output_selector:
        try:
            output_elems = driver.find_elements(By.CSS_SELECTOR, output_selector)
            output_count = len(output_elems)
            for el in output_elems:
                try:
                    txt = (el.text or "").strip()
                except Exception:
                    txt = ""
                if txt:
                    sample_text = txt
            if not sample_text and output_elems:
                sample_text = "<output selector matched elements, but no visible text yet>"
        except Exception as exc:
            return False, f"Output selector is invalid: {output_selector!r}. Error: {exc}", ""

    ok = bool(input_selector and output_selector and input_count > 0 and output_count > 0)
    message = f"input_matches={input_count}; output_matches={output_count}"
    return ok, message, sample_text


def _send_calibration_probe(
    driver: webdriver.Chrome,
    input_selector: Optional[str],
    send_selector: Optional[str],
    frame_selector: Optional[str],
    wait_time: int = 10,
) -> None:
    if not input_selector:
        raise RuntimeError("Cannot send calibration probe without an input selector.")
    _switch_to_frame(driver, frame_selector, wait_time=wait_time)
    input_el = WebDriverWait(driver, wait_time).until(lambda d: d.find_element(By.CSS_SELECTOR, input_selector))
    input_el.click()
    try:
        input_el.clear()
    except Exception:
        pass
    input_el.send_keys(f"Please reply exactly with: {CALIBRATION_SENTINEL}")
    if send_selector:
        driver.find_element(By.CSS_SELECTOR, send_selector).click()
    else:
        input_el.send_keys(Keys.ENTER)


def _show_candidate_output_nodes(console: Any, driver: webdriver.Chrome, frame_selector: Optional[str], wait_time: int = 10) -> None:
    try:
        _switch_to_frame(driver, frame_selector, wait_time=wait_time)
    except Exception as exc:
        _print(console, f"Cannot inspect candidate nodes because frame selector failed: {exc}", "red")
        return

    candidates: list[tuple[str, str]] = []
    for css in ["p", "div", "span", "pre", "article", "section", "li"]:
        try:
            for el in driver.find_elements(By.CSS_SELECTOR, css):
                try:
                    if not el.is_displayed():
                        continue
                    text = (el.text or "").strip()
                    if len(text) < 3:
                        continue
                    selector = _build_css_selector(el)
                    if (selector, text) not in candidates:
                        candidates.append((selector, text))
                except Exception:
                    continue
        except Exception:
            continue

    # Prefer meaningful longer nodes, but keep the list short.
    candidates.sort(key=lambda item: len(item[1]), reverse=True)
    candidates = candidates[:12]

    if not candidates:
        _print(console, "No visible text candidates found in the current page context.", "yellow")
        return

    if console and Table:
        table = Table(title="Candidate Output Nodes", show_lines=True)
        table.add_column("#", justify="right", style="bold green", width=4)
        table.add_column("Selector", overflow="fold")
        table.add_column("Text sample", overflow="fold")
        for idx, (selector, text) in enumerate(candidates, 1):
            table.add_row(str(idx), selector, _short(text, 200))
        console.print(table)
    else:
        for idx, (selector, text) in enumerate(candidates, 1):
            print(f"[{idx}] {selector}\n    {_short(text, 200)}")


def _run_auto_selector(console: Any, driver: webdriver.Chrome, wait_time: int = 20) -> dict[str, Any]:
    if AutoSelector is None:
        _print(console, "AutoSelector is not available in this installation.", "yellow")
        return {"status": "failed"}
    try:
        detector = AutoSelector(driver, wait_time=wait_time)
        result = detector.detect()
        data = result.to_dict() if hasattr(result, "to_dict") else dict(result)  # type: ignore[arg-type]
        return data
    except Exception as exc:
        _print(console, f"Auto-selector failed: {exc}", "yellow")
        return {"status": "failed", "error": str(exc)}


def calibrate_target_selectors(
    target: TargetDefinition,
    console: Any = None,
    save: bool = True,
    wait_time: int = 20,
) -> TargetDefinition:
    """Assisted target selector calibration.

    This function intentionally keeps Chrome open when auto-detection is partial,
    so the tester can inspect the DOM manually and paste the missing selector.
    """
    _print(console, "\n[bold green]Target selector calibration[/bold green]")
    _print(console, f"Target: {target.name} — {target.url}", "dim")
    _print(console, "Chrome will open in visible mode so you can inspect the target if needed.", "dim")

    driver = _open_driver(target.url, headless=False)
    should_quit = True

    input_selector = _selector_value(target.input_selector)
    output_selector = _selector_value(target.output_selector)
    send_selector = _selector_value(target.send_selector)
    frame_selector = _selector_value(target.frame_selector)

    try:
        if _confirm("Try automatic selector discovery now?", default=True):
            data = _run_auto_selector(console, driver, wait_time=wait_time)
            input_selector = _selector_value(data.get("input_selector")) or input_selector
            output_selector = _selector_value(data.get("output_selector")) or output_selector
            frame_selector = _selector_value(data.get("frame_selector")) or frame_selector
            status = data.get("status") or "unknown"
            notes = data.get("notes") or data.get("details") or []
            _print(console, f"Auto-selector status: {status}", "green" if output_selector else "yellow")
            if notes:
                _print(console, f"Notes: {notes}", "dim")

        while True:
            ok, message, sample = _validate_selectors(driver, input_selector, output_selector, frame_selector, wait_time=5)
            _print(console, f"Current selector validation: {message}", "green" if ok else "yellow")
            if sample:
                _print(console, f"Output sample: {_short(sample, 240)}", "dim")

            if ok:
                break

            if not input_selector:
                input_selector = _selector_value(_prompt("Input selector", default=""))
                continue

            _print(console, "\nOutput selector is missing or not matching visible response text.", "yellow")
            _print(console, "The browser is still open. You can now:", "dim")
            _print(console, "  1. Send/submit a prompt manually if needed", "dim")
            _print(console, "  2. Right-click the response area → Inspect", "dim")
            _print(console, "  3. Copy selector and paste it below", "dim")

            if _confirm("Send a safe calibration probe from TrustInspect?", default=False):
                try:
                    _send_calibration_probe(driver, input_selector, send_selector, frame_selector, wait_time=wait_time)
                    _print(console, "Calibration probe sent. Wait for the target response, then paste/inspect selector.", "green")
                except Exception as exc:
                    _print(console, f"Could not send calibration probe: {exc}", "red")

            if _confirm("Show visible candidate output nodes?", default=True):
                _show_candidate_output_nodes(console, driver, frame_selector, wait_time=wait_time)

            pasted_output = _selector_value(_prompt("Output selector", default=output_selector or ""))
            if pasted_output:
                output_selector = pasted_output

            pasted_input = _selector_value(_prompt("Input selector", default=input_selector or ""))
            if pasted_input:
                input_selector = pasted_input

            pasted_send = _selector_value(_prompt("Send button selector (optional)", default=send_selector or ""))
            send_selector = pasted_send

            pasted_frame = _selector_value(_prompt("Frame selector (optional)", default=frame_selector or ""))
            frame_selector = pasted_frame

            ok, message, sample = _validate_selectors(driver, input_selector, output_selector, frame_selector, wait_time=5)
            _print(console, f"Selector validation: {message}", "green" if ok else "yellow")
            if sample:
                _print(console, f"Output sample: {_short(sample, 240)}", "dim")
            if ok:
                break

            if _confirm("Continue calibration?", default=True):
                continue
            break

        calibrated = replace(
            target,
            status="ready" if input_selector and output_selector else "selector_required",
            input_selector=input_selector,
            output_selector=output_selector,
            send_selector=send_selector,
            frame_selector=frame_selector,
        )

        if not calibrated.is_ready:
            _print(console, "Target is still not ready: both input and output selectors are required.", "red")
            _print(console, "Tip: do not enter 'null' for missing selectors; keep Chrome open and inspect manually.", "dim")
            return calibrated

        if save and _confirm("Save this calibrated target locally?", default=True):
            path = save_local_target(calibrated)
            _print(console, f"[+] Target saved to {path}", "green")

        return calibrated

    finally:
        if _confirm("Close calibration browser now?", default=True):
            try:
                driver.quit()
            except Exception:
                pass
        else:
            should_quit = False
            _print(console, "Calibration browser left open. Close it manually when finished.", "yellow")
        if should_quit:
            pass
