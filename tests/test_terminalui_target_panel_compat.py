def test_terminalui_target_panel_accepts_current_cli_call():
    from trustinspect.ui.terminal import TerminalUI

    ui = TerminalUI(no_banner=True)
    # Current CLI call style must not raise:
    ui.target_panel(
        "http://127.0.0.1:8080/",
        "127.0.0.1",
        "reports/127_0_0_1_adaptive_tests.yaml",
        mode="adaptive-web-ui",
    )
