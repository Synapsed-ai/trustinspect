from trustinspect.ui.terminal import TerminalUI


def test_terminalui_exposes_cli_aliases():
    ui = TerminalUI(quiet=True)
    assert hasattr(ui, "banner")
    assert hasattr(ui, "render_banner")
    assert hasattr(ui, "handle_event")
    assert hasattr(ui, "target_panel")
    assert hasattr(ui, "final_summary")
    ui.banner(version="v-test", license_name="Apache-2.0")
    ui.handle_event({"type": "test_start", "index": 1, "total": 1, "test_id": "T", "test_name": "N"})
