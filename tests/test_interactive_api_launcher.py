"""The local API workflow must work without browser selectors or PATH setup."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from trustinspect.interactive import launcher


@pytest.mark.parametrize("suite", launcher.SUITES)
def test_api_commands_use_packaged_suite_ids_and_current_interpreter(suite, monkeypatch):
    interpreter = "/a virtual environment/bin/python"
    monkeypatch.setattr(sys, "executable", interpreter)
    cmd = launcher._build_api_scan_command(
        "http://127.0.0.1:1234/v1", "publisher/a model", suite,
        1, 3, 180, 2048, True,
    )
    assert cmd[:4] == [interpreter, "-m", "trustinspect.cli", "scan-api"]
    assert cmd[cmd.index("--suite") + 1] == suite["id"]
    assert cmd[cmd.index("--model") + 1] == "publisher/a model"
    assert cmd[cmd.index("--dynamic-tests-per-static") + 1] == "1"
    assert cmd[cmd.index("--max-dynamic-tests") + 1] == "3"
    output = Path(cmd[cmd.index("--output") + 1])
    assert output.parent == Path("reports")
    assert output.name.startswith("publisher-a-model_")
    assert "--open" in cmd
    for web_option in ("--headless", "--target-url", "--input-selector", "--output-selector", "--send-selector", "--frame-selector"):
        assert web_option not in cmd


def test_api_static_command_omits_unused_dynamic_cap():
    cmd = launcher._build_api_scan_command(
        "http://127.0.0.1:1234/v1", "qwen3-32b", launcher.SUITES[1],
        0, None, 240, 4096, False,
    )
    assert cmd[cmd.index("--dynamic-tests-per-static") + 1] == "0"
    assert "--max-dynamic-tests" not in cmd
    assert "--open" not in cmd


def _wizard(monkeypatch, *, run=True, timeout=180, max_tokens=2048, dynamic=(0, None)):
    prompts = []
    dynamic_defaults = []
    displayed = []
    executed = []
    monkeypatch.setattr(launcher, "_console", lambda: None)

    def prompt(label, default=None):
        prompts.append(label)
        return default

    monkeypatch.setattr(launcher, "_prompt", prompt)
    monkeypatch.setattr(launcher, "_choose_suite", lambda: launcher.SUITES[1])
    monkeypatch.setattr(launcher, "_choose_dynamic", lambda default=1: (dynamic_defaults.append(default) or dynamic))
    monkeypatch.setattr(launcher, "_int_prompt", lambda label, default=0: timeout if "Timeout" in label else max_tokens)
    monkeypatch.setattr(launcher, "_confirm", lambda label, default=False: run if label == "Run now?" else True)
    monkeypatch.setattr(launcher, "_command_panel", lambda console, command: displayed.append(command))
    monkeypatch.setattr(launcher.subprocess, "run", lambda command: executed.append(command))

    def no_browser(*args, **kwargs):
        pytest.fail("API assessment attempted browser target selection or calibration")

    monkeypatch.setattr(launcher, "_choose_target", no_browser)
    monkeypatch.setattr(launcher, "_calibrate_target", no_browser)
    launcher._run_api_assessment()
    return prompts, dynamic_defaults, displayed, executed


def test_api_wizard_previews_exact_executed_command_and_defaults_to_static(monkeypatch):
    prompts, defaults, displayed, executed = _wizard(monkeypatch)
    assert prompts == ["API base URL", "Model (API Identifier)"]
    assert defaults == [0]
    assert len(executed) == 1
    assert displayed == executed
    assert executed[0][:4] == [sys.executable, "-m", "trustinspect.cli", "scan-api"]


def test_api_wizard_cancel_does_not_launch(monkeypatch):
    _, _, displayed, executed = _wizard(monkeypatch, run=False)
    assert len(displayed) == 1
    assert executed == []


@pytest.mark.parametrize(("timeout", "max_tokens"), [(0, 2048), (-1, 2048), (180, 0), (180, -1)])
def test_api_wizard_rejects_nonpositive_limits(monkeypatch, timeout, max_tokens):
    _, _, displayed, executed = _wizard(monkeypatch, timeout=timeout, max_tokens=max_tokens)
    assert displayed == []
    assert executed == []


@pytest.mark.parametrize("cap", [0, -1])
def test_api_wizard_rejects_nonpositive_dynamic_cap(monkeypatch, capsys, cap):
    _, _, displayed, executed = _wizard(monkeypatch, dynamic=(1, cap))
    assert displayed == []
    assert executed == []
    assert "Choose Static only for zero dynamic tests" in capsys.readouterr().out


def test_launcher_keeps_exit_option_and_routes_new_api_option(monkeypatch):
    choices = iter([6, 5])
    visited = []
    monkeypatch.setattr(launcher, "_console", lambda: None)
    monkeypatch.setattr(launcher, "_int_prompt", lambda *args, **kwargs: next(choices))
    monkeypatch.setattr(launcher, "_run_api_assessment", lambda: visited.append("api"))
    launcher.run_interactive_launcher()
    assert visited == ["api"]
