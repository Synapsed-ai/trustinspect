from pathlib import Path


def test_rich_declared_as_runtime_dependency():
    text = Path('pyproject.toml').read_text(encoding='utf-8').lower()
    assert 'rich' in text


def test_terminal_ui_imports_after_packaging_install():
    from trustinspect.ui.terminal import TerminalUI

    ui = TerminalUI()
    assert ui.console is not None
