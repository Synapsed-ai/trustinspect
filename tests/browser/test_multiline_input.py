"""Real browser input-contract checks; no remote model requests."""
from __future__ import annotations

import os
import shutil

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("TRUSTINSPECT_BROWSER_TESTS") != "1",
                               reason="Opt-in real Chrome input tests")


@pytest.fixture
def browser():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    executable = shutil.which("chromedriver")
    assert executable, "Real ChromeDriver is required"
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(executable), options=options)
    yield driver
    driver.quit()


@pytest.mark.parametrize("element", ["textarea", "contenteditable", "iframe"])
@pytest.mark.parametrize("payload", ["first line\n\nsecond line", "one\r\ntwo\rthree", "literal [bold] \"quoted\"\n<not-a-tag> é"])
def test_multiline_text_is_inserted_once_without_keyboard_submission(browser, element, payload):
    from selenium.webdriver.common.by import By
    from trustinspect.scanners.web_ui.robust_actions import set_input_text
    browser.get("about:blank")
    if element == "iframe":
        browser.execute_script("document.body.innerHTML='<iframe id=frame></iframe>'")
        browser.switch_to.frame(browser.find_element(By.ID, "frame"))
    browser.execute_script("""
        document.body.innerHTML = arguments[0] === 'contenteditable'
            ? '<div id=input contenteditable=true></div><button id=send>Send</button>'
            : '<textarea id=input></textarea><button id=send>Send</button>';
        window.sent = []; window.keys = 0; window.inputs = 0;
        const input = document.querySelector('#input');
        const read = () => 'value' in input ? input.value : input.textContent;
        const send = () => { window.sent.push(read()); };
        input.addEventListener('keydown', e => {
            window.keys++; if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}
        });
        input.addEventListener('input', () => window.inputs++);
        document.querySelector('#send').addEventListener('click', send);
    """, element)
    target = browser.find_element(By.ID, "input")
    set_input_text(browser, target, payload)
    expected = payload.replace("\r\n", "\n").replace("\r", "\n")
    assert browser.execute_script("return window.sent") == []
    assert browser.execute_script("return window.keys") == 0
    assert browser.execute_script("return window.inputs") >= 1
    browser.find_element(By.ID, "send").click()
    assert browser.execute_script("return window.sent") == [expected]


def test_readonly_multiline_input_is_not_overwritten(browser):
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import JavascriptException
    from trustinspect.scanners.web_ui.robust_actions import set_input_text
    browser.get("about:blank")
    browser.execute_script("document.body.innerHTML='<textarea id=input readonly>original</textarea>'")
    target = browser.find_element(By.ID, "input")
    with pytest.raises(JavascriptException, match="not editable"):
        set_input_text(browser, target, "first\nsecond")
    assert target.get_attribute("value") == "original"
