def test_terminalui_target_panel_accepts_new_cli_call_style():
    from trustinspect.ui.terminal import TerminalUI

    ui = TerminalUI(no_banner=True)
    # Must not raise: this is the adaptive-scan call style.
    ui.target_panel(
        "http://127.0.0.1:8080/",
        "127.0.0.1",
        "reports/127_0_0_1_adaptive_tests.yaml",
        mode="adaptive-web-ui",
    )


def test_terminalui_target_panel_accepts_legacy_call_style():
    from trustinspect.ui.terminal import TerminalUI

    ui = TerminalUI(no_banner=True)
    # Must not raise: older call style used by scan-web/reporting helpers.
    ui.target_panel(
        "127.0.0.1",
        "http://127.0.0.1:8080/",
        "web-ui",
        "suites/owasp/aitg-light.yaml",
    )
