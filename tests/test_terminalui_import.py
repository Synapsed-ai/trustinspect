def test_terminalui_imports_and_constructs():
    from trustinspect.ui.terminal import TerminalUI, make_console, render_banner
    ui = TerminalUI(enabled=False)
    assert ui is not None
    assert callable(make_console)
    assert callable(render_banner)
