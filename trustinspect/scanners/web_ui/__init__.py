from __future__ import annotations

__all__ = ["WebUiScanner"]


def __getattr__(name: str):
    if name == "WebUiScanner":
        from trustinspect.scanners.web_ui.selenium_scanner import WebUiScanner
        return WebUiScanner
    raise AttributeError(name)
