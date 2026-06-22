from trustinspect.ui.terminal import TerminalUI


def test_terminalui_target_panel_accepts_keyword_test_cases():
    ui = TerminalUI(quiet=True) if "quiet" in getattr(TerminalUI.__init__, "__annotations__", {}) else TerminalUI()
    # Should not raise. This is the calling convention used by CLI adaptive-scan.
    ui.target_panel(
        "127.0.0.1",
        "http://127.0.0.1:8080/",
        mode="adaptive-web-ui",
        test_cases="reports/127_0_0_1_adaptive_tests.yaml",
    )
