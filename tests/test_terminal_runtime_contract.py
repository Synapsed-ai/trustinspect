"""Exercise effective UI methods after legacy compatibility wrappers are installed."""
import io
import os
import subprocess
import sys
import pytest
from rich.console import Console
from trustinspect.ui.terminal import TerminalUI, TI_THEME


def ui(**options):
    stream = io.StringIO()
    return TerminalUI(console=Console(file=stream, theme=TI_THEME, width=120, color_system=None), **options), stream


def exercise(instance):
    instance.banner()
    instance.target_panel("local", "http://127.0.0.1", "web-ui", "suite.yaml")
    instance.info("status")
    instance.handle_event({"type": "test_start", "index": 1, "total": 1, "test_id": "T", "prompt": "prompt"})
    instance.render_progress_event({"type": "test_result", "index": 1, "total": 1, "classification": "SAFE", "response": "answer"})
    instance.final_summary(1, 1, 0, 0, 1, 0, "report.html")


@pytest.mark.parametrize("flags", [
    {"quiet": True}, {"quiet_ui": True}, {"enabled": False},
    {"quiet": True, "enabled": True}, {"quiet_ui": True, "show_banner": True},
])
def test_quiet_aliases_suppress_all_live_ui(flags):
    instance, stream = ui(**flags)
    exercise(instance)
    assert stream.getvalue() == ""


@pytest.mark.parametrize("flags", [{"no_banner": True}, {"show_banner": False}, {"no_banner": True, "show_banner": True}])
def test_no_banner_preserves_other_ui(flags):
    instance, stream = ui(**flags)
    instance.banner()
    assert stream.getvalue() == ""
    instance.target_panel("local", "http://127.0.0.1", "web-ui", "suite.yaml")
    assert "Assessment Target" in stream.getvalue()


@pytest.mark.parametrize("flag,field,event_type", [("show_full_prompt", "prompt", "test_start"), ("show_full_response", "response", "test_result")])
def test_full_evidence_flags_preserve_tail(flag, field,event_type):
    instance, stream = ui(**{flag: True})
    instance.handle_event({"type": event_type, "index": 1, "total": 1, field: "a" * 1400 + "TAIL_MARKER", "classification": "SAFE"})
    assert "TAIL_MARKER" in stream.getvalue()


def test_target_markup_is_literal_evidence():
    instance, stream = ui()
    instance.handle_event({"type": "test_result", "response": "[bold]literal[/bold]", "classification": "SAFE"})
    assert "[bold]literal[/bold]" in stream.getvalue()


def test_module_cli_has_no_import_order_warning():
    result = subprocess.run([sys.executable, "-Werror::RuntimeWarning", "-m", "trustinspect.dynamic.engine", "--help"],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "RuntimeWarning" not in result.stderr


def test_lazy_exports_remain_available():
    from trustinspect.dynamic import DynamicTestEngine, generate_dynamic_tests, generate_dynamic_tests_for_static_suite
    assert all(callable(x) for x in [DynamicTestEngine, generate_dynamic_tests, generate_dynamic_tests_for_static_suite])
