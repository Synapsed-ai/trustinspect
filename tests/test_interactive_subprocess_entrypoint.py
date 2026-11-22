"""Regression: interactive subprocesses must not depend on an activated venv."""
from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace

import pytest

from trustinspect.interactive import launcher


def _target():
    return SimpleNamespace(
        id="local_fixture",
        name="Local fixture",
        url="https://example.invalid/",
        input_selector="#input",
        output_selector="#output",
        send_selector="#send",
        frame_selector=None,
    )


@pytest.mark.parametrize(
    ("dynamic_per_static", "subcommand"),
    [(0, "scan-web"), (1, "adaptive-scan")],
)
def test_assessment_command_uses_venv_interpreter(dynamic_per_static, subcommand):
    suite = {"id": "owasp-llm-top10-2025-light", "mode": "suite", "value": "owasp-llm-top10-2025-light"}
    cmd = launcher._build_scan_command(_target(), suite, dynamic_per_static, None, True, False)
    assert cmd[:4] == [sys.executable, "-m", "trustinspect.cli", subcommand]
    assert "--target-url" in cmd and "--input-selector" in cmd
    if dynamic_per_static:
        assert "--dynamic-tests-per-static" in cmd
    else:
        assert "--dynamic-tests-per-static" not in cmd


def test_run_assessment_executes_same_interpreter_without_path_lookup(monkeypatch):
    suite = {"id": "owasp-llm-top10-2025-light", "mode": "suite", "value": "owasp-llm-top10-2025-light"}
    monkeypatch.setattr(launcher, "_choose_target", _target)
    monkeypatch.setattr(launcher, "_choose_suite", lambda: suite)
    monkeypatch.setattr(launcher, "_choose_dynamic", lambda: (1, None))
    monkeypatch.setattr(launcher, "_confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(launcher, "_console", lambda: None)
    displayed = []
    monkeypatch.setattr(launcher, "_command_panel", lambda console, command: displayed.append(command))
    executed = []
    monkeypatch.setattr(launcher.subprocess, "run", lambda command: executed.append(command))
    launcher._run_known_target_assessment()
    assert len(executed) == 1
    assert executed == displayed
    assert executed[0][:4] == [sys.executable, "-m", "trustinspect.cli", "adaptive-scan"]


def test_profile_target_executes_same_interpreter_without_path_lookup(monkeypatch):
    monkeypatch.setattr(launcher, "_choose_target", _target)
    monkeypatch.setattr(launcher, "_confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(launcher, "_console", lambda: None)
    displayed = []
    monkeypatch.setattr(launcher, "_command_panel", lambda console, command: displayed.append(command))
    executed = []
    monkeypatch.setattr(launcher.subprocess, "run", lambda command: executed.append(command))
    launcher._profile_only()
    assert executed == displayed
    assert len(executed) == 1
    assert executed[0][:4] == [sys.executable, "-m", "trustinspect.cli", "profile-target"]


def test_module_entrypoint_works_without_global_console_script_on_path():
    result = subprocess.run(
        [sys.executable, "-m", "trustinspect.cli", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "adaptive-scan" in result.stdout
    assert "scan-web" in result.stdout
