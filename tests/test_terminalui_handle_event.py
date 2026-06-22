from trustinspect.ui.terminal import TerminalUI


def test_terminalui_exposes_handle_event():
    ui = TerminalUI(quiet=True)
    assert callable(ui.handle_event)
    ui.handle_event({"type": "test_start", "index": 1, "total": 1, "test_id": "T1", "test_name": "Test"})


def test_terminalui_handles_result_event_without_crashing():
    ui = TerminalUI(quiet=True)
    ui.handle_event({
        "type": "test_result",
        "index": 1,
        "total": 1,
        "prompt": "hello",
        "response": "world",
        "classification": "SAFE",
        "confidence": 0.9,
        "rationale": "ok",
    })
