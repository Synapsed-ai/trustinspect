def test_terminal_ui_importable_and_progress_aliases_exist():
    from trustinspect.ui.terminal import TerminalUI

    ui = TerminalUI()
    assert ui.console is not None
    assert callable(ui.render_banner)
    assert callable(ui.handle_event)
    assert callable(ui.render_progress_event)
