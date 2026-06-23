from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class SelectorResult:
    input_selector: Optional[str]
    output_selector: Optional[str]
    frame_selector: Optional[str] = None
    status: str = "unknown"
    notes: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_selector": self.input_selector,
            "output_selector": self.output_selector,
            "frame_selector": self.frame_selector,
            "status": self.status,
            "notes": self.notes or [],
        }


class AutoSelector:
    """Best-effort selector discovery for Web UI LLM/chat targets."""

    def __init__(self, driver: WebDriver, wait_time: int = 15) -> None:
        self.driver = driver
        self.wait_time = wait_time

    def detect(self, sentinel_text: str = "SYNINSPECT_SELECTOR_PING") -> SelectorResult:
        notes: list[str] = []
        input_el = self.detect_input_element()
        if input_el is None:
            return SelectorResult(None, None, status="failed", notes=["No visible input candidate found."])

        input_selector = self.build_css_selector(input_el)
        notes.append(f"Selected input candidate: {input_selector}")

        output_selector = self.detect_output_selector(input_el, sentinel_text=sentinel_text)
        if not output_selector:
            return SelectorResult(input_selector, None, status="partial", notes=notes + ["Could not identify output selector."])

        return SelectorResult(input_selector, output_selector, status="ok", notes=notes)

    def detect_input_element(self) -> Optional[Any]:
        candidates: list[Any] = []
        candidates.extend(self.driver.find_elements(By.TAG_NAME, "textarea"))

        for el in self.driver.find_elements(By.TAG_NAME, "input"):
            input_type = (el.get_attribute("type") or "").lower()
            if input_type in ("", "text", "search", "email"):
                candidates.append(el)

        candidates.extend(self.driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']"))

        best = None
        best_score = -1
        for el in candidates:
            try:
                if not el.is_displayed() or not el.is_enabled():
                    continue
            except Exception:
                continue

            score = self._score_input(el)
            if score > best_score:
                best_score = score
                best = el

        return best

    def detect_output_selector(self, input_el: Any, sentinel_text: str) -> Optional[str]:
        before = self._capture_visible_texts()
        input_el.click()
        try:
            input_el.clear()
        except Exception:
            pass
        input_el.send_keys(sentinel_text)
        input_el.send_keys(Keys.ENTER)

        time.sleep(1)
        try:
            WebDriverWait(self.driver, self.wait_time).until(lambda d: self._has_new_text(before))
        except Exception:
            return None

        new_nodes = self._new_text_nodes(before)
        # Drop user echo and overly short nodes.
        new_nodes = [n for n in new_nodes if sentinel_text not in n["text"] and len(n["text"].strip()) > 2]
        if not new_nodes:
            return None

        # Heuristic: bot response is usually one of the longest newly-visible text nodes.
        new_nodes.sort(key=lambda item: len(item["text"]), reverse=True)
        target_el = new_nodes[0]["element"]
        return self.build_css_selector(target_el, use_last_child=True)

    def _score_input(self, el: Any) -> int:
        score = 0
        tag = (el.tag_name or "").lower()
        if tag == "textarea":
            score += 5
        if tag == "input":
            score += 3
        if (el.get_attribute("contenteditable") or "").lower() == "true":
            score += 4

        meta = " ".join(
            [
                el.get_attribute("id") or "",
                el.get_attribute("class") or "",
                el.get_attribute("placeholder") or "",
                el.get_attribute("aria-label") or "",
                el.get_attribute("name") or "",
            ]
        ).lower()
        for kw in ["chat", "message", "messaggio", "scrivi", "ask", "prompt", "input", "send"]:
            if kw in meta:
                score += 2
        return score

    def _capture_visible_texts(self) -> set[str]:
        texts: set[str] = set()
        for el in self.driver.find_elements(By.XPATH, "//*[normalize-space(text())!='']"):
            try:
                if el.is_displayed():
                    txt = el.text.strip()
                    if txt:
                        texts.add(txt)
            except Exception:
                continue
        return texts

    def _has_new_text(self, before: set[str]) -> bool:
        return bool(self._new_text_nodes(before))

    def _new_text_nodes(self, before: set[str]) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        for el in self.driver.find_elements(By.XPATH, "//*[normalize-space(text())!='']"):
            try:
                if not el.is_displayed():
                    continue
                txt = el.text.strip()
                if txt and txt not in before:
                    nodes.append({"element": el, "text": txt})
            except Exception:
                continue
        return nodes

    def build_css_selector(self, element: Any, use_last_child: bool = False) -> str:
        # Prefer stable IDs when available.
        el_id = element.get_attribute("id")
        if el_id:
            return f"#{self._css_escape(el_id)}"

        parts: list[str] = []
        el = element
        depth = 0
        while el is not None and depth < 6:
            tag = (el.tag_name or "div").lower()
            el_id = el.get_attribute("id")
            classes = (el.get_attribute("class") or "").strip().split()

            if el_id:
                parts.append(f"#{self._css_escape(el_id)}")
                break

            stable = self._stable_classes(classes)
            if stable:
                part = tag + "".join(f".{self._css_escape(c)}" for c in stable[:2])
            else:
                part = tag

            if depth == 0 and use_last_child:
                part += ":last-child"
            parts.append(part)

            try:
                el = el.find_element(By.XPATH, "..")
            except Exception:
                break
            depth += 1

        parts.reverse()
        return " ".join(parts)

    def _stable_classes(self, classes: list[str]) -> list[str]:
        stable = []
        for c in classes:
            if len(c) < 3:
                continue
            # keep semantic classes; avoid short generated utility classes when possible
            if any(token in c.lower() for token in ["chat", "message", "bubble", "assistant", "bot", "response", "text", "webchat", "iaw"]):
                stable.append(c)
        if stable:
            return stable
        return [c for c in classes if len(c) > 4][:2]

    def _css_escape(self, value: str) -> str:
        return value.replace(".", "\\.").replace(":", "\\:").replace("#", "\\#")


def open_driver(url: str, headless: bool = False) -> WebDriver:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1100")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(45)
    driver.get(url)
    return driver


def detect_selectors(url: str, wait_time: int = 15, headless: bool = False) -> SelectorResult:
    driver = open_driver(url, headless=headless)
    try:
        detector = AutoSelector(driver, wait_time=wait_time)
        return detector.detect()
    finally:
        driver.quit()
