from __future__ import annotations

import time
from typing import Any, Iterable, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


NULLISH = {"", "none", "null", "nil", "n/a", "na", "-", "undefined"}


def optional_selector(value: Any) -> Optional[str]:
    if value is None:
        return None
    value = str(value).strip()
    if value.lower() in NULLISH:
        return None
    return value


DEFAULT_BLOCKING_SELECTORS = [
    "#hs-eu-cookie-settings-button",
    "#hs-eu-cookie-confirmation",
    "#onetrust-banner-sdk",
    "#onetrust-consent-sdk",
    ".onetrust-pc-dark-filter",
    "button[aria-label*='cookie' i]",
    "button[id*='cookie' i]",
    "div[id*='cookie' i]",
]


def _target_metadata(target: Any) -> dict[str, Any]:
    meta = getattr(target, "metadata", None)
    return meta if isinstance(meta, dict) else {}


def configured_overlay_selectors(target: Any = None) -> list[str]:
    meta = _target_metadata(target)
    preflight = meta.get("preflight") if isinstance(meta.get("preflight"), dict) else {}
    selectors = []
    for key in ("dismiss_cookie_selectors", "hide_overlay_selectors", "blocking_overlay_selectors"):
        value = preflight.get(key)
        if isinstance(value, str):
            selectors.append(value)
        elif isinstance(value, list):
            selectors.extend(str(v) for v in value if str(v).strip())
    return list(dict.fromkeys(DEFAULT_BLOCKING_SELECTORS + selectors))


def dismiss_blocking_overlays(driver, target: Any = None) -> None:
    """Best-effort dismissal/hiding of cookie banners and floating controls.

    This is deliberately conservative: it first tries common accept/close buttons,
    then hides known blocking elements using JS. It should never raise.
    """
    try:
        for selector in [
            "button[id*='accept' i]",
            "button[class*='accept' i]",
            "button[aria-label*='accept' i]",
            "button[aria-label*='close' i]",
            "button[class*='close' i]",
        ]:
            for el in driver.find_elements(By.CSS_SELECTOR, selector)[:3]:
                try:
                    if el.is_displayed() and el.is_enabled():
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(0.1)
                except Exception:
                    pass
    except Exception:
        pass

    for selector in configured_overlay_selectors(target):
        try:
            driver.execute_script(
                """
                for (const el of document.querySelectorAll(arguments[0])) {
                    el.style.setProperty('display', 'none', 'important');
                    el.style.setProperty('visibility', 'hidden', 'important');
                    el.style.setProperty('pointer-events', 'none', 'important');
                }
                """,
                selector,
            )
        except Exception:
            pass


def prepare_input_element(driver, input_el, wait_time: int = 20, target: Any = None):
    dismiss_blocking_overlays(driver, target)
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", input_el)
        time.sleep(0.1)
    except Exception:
        pass

    def ready(_driver):
        try:
            return input_el.is_displayed() and input_el.is_enabled()
        except Exception:
            return False

    WebDriverWait(driver, wait_time).until(ready)
    try:
        input_el.click()
    except Exception:
        dismiss_blocking_overlays(driver, target)
        driver.execute_script("arguments[0].focus();", input_el)
    return input_el


def set_input_text(driver, input_el, value: str) -> None:
    value = value or ""
    try:
        input_el.clear()
    except Exception:
        pass
    try:
        input_el.send_keys(value)
        return
    except Exception:
        pass

    # JS fallback for textarea/input/contenteditable components.
    driver.execute_script(
        """
        const el = arguments[0];
        const value = arguments[1];
        el.focus();
        if ('value' in el) {
            el.value = value;
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
        } else {
            el.textContent = value;
            el.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: 'insertText', data: value}));
        }
        """,
        input_el,
        value,
    )
