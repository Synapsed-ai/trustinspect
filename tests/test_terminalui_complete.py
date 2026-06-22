def test_terminalui_has_cli_methods():
    from trustinspect.ui.terminal import TerminalUI

    ui = TerminalUI(quiet=True)
    assert hasattr(ui, "banner")
    assert hasattr(ui, "target_panel")
    assert hasattr(ui, "handle_event")
    assert hasattr(ui, "final_summary")


def test_interactive_suite_choices_include_aitg_light_and_full():
    from trustinspect.interactive.launcher import SUITES

    ids = {suite["id"] for suite in SUITES}
    assert "owasp-aitg-light" in ids
    assert "owasp-aitg-full" in ids
    assert "owasp-aitg-32" not in ids
