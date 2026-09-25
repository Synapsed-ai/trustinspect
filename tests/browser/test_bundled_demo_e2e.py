"""Run the public CLI and real Selenium against the bundled demo HTTP handler."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import threading
from http.server import ThreadingHTTPServer

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("TRUSTINSPECT_BROWSER_TESTS") != "1",
                               reason="Opt-in Chrome/ChromeDriver end-to-end campaign")
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(params=["vulnerable", "hardened"])
def bundled_demo(request):
    spec = importlib.util.spec_from_file_location("bundled_demo_e2e", ROOT / "demos/trustinspect-demo-chatbot/app/main.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = ThreadingHTTPServer(("127.0.0.1", 0), module.DemoHandler)
    server.demo_mode = request.param
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield module, request.param, f"http://127.0.0.1:{server.server_address[1]}/"
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


@pytest.mark.parametrize("adaptive", [False, True], ids=["static", "adaptive"])
def test_cli_records_actual_bundled_demo_behavior(bundled_demo, adaptive, tmp_path, monkeypatch, capsys):
    from trustinspect import cli
    from webdriver_manager.chrome import ChromeDriverManager
    executable = shutil.which("chromedriver")
    assert executable, "Requested end-to-end campaign requires a real ChromeDriver"
    monkeypatch.setattr(ChromeDriverManager, "install", lambda self: executable)
    module, mode, url = bundled_demo
    artifact_dir = Path(os.environ.get("TI_BROWSER_EVIDENCE_DIR", str(tmp_path))).resolve()
    output = artifact_dir / f"bundled-{mode}-{'adaptive' if adaptive else 'static'}.html"
    args = ["trustinspect", "adaptive-scan" if adaptive else "scan-web", "--suite", "owasp-llm-top10-2025-light",
            "--target-url", url, "--input-selector", "#chatInput", "--output-selector", "#chat-content .bot-message p",
            "--send-selector", "#sendButton", "--headless", "--quiet-ui", "--no-banner", "--wait-time", "5",
            "--output", str(output)]
    if adaptive:
        args += ["--dynamic-tests-per-static", "1", "--max-dynamic-tests", "4",
                 "--target-profile", str(ROOT / "demos/trustinspect-demo-chatbot/target_profile.yaml"),
                 "--generated-tests-output", str(output.with_suffix(".generated.yaml"))]
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", args)
    cli.main()  # No substitution of scanner, analyzer, finding engine or reporter.
    data = json.loads(output.with_suffix(".json").read_text(encoding="utf-8"))
    observations = data["observations"]
    assert len(observations) == (14 if adaptive else 10)
    for observation in observations:
        assert observation["classification"] != "ERROR", observation["rationale"]
        values = {e["evidence_type"]: e["value"] for e in observation["evidence"]}
        assert values["response"] == module.build_response(values["prompt"], mode), observation["test_case"]["id"]
        assert Path(values["screenshot"]).is_file()
    confirmed = {o["test_case"]["id"] for o in observations if o["classification"] == "VULNERABILITY"}
    assert len(data["findings"]) == len(confirmed)
    if mode == "hardened":
        assert confirmed == set()
    else:
        assert {"OWASP-LLM01-LIGHT-001", "OWASP-LLM08-LIGHT-001"} <= confirmed
        raw_echo = next(o for o in observations if o["test_case"]["id"] == "OWASP-LLM05-LIGHT-001")
        assert raw_echo["classification"] == "POSSIBLE VULNERABILITY", "Text echo is not proof of XSS execution"
        if not adaptive:
            assert len(confirmed) == 2
    if adaptive:
        assert sum(bool(o["test_case"]["metadata"].get("parent_static_test_id")) for o in observations) == 4
    out = capsys.readouterr().out
    assert "Evidence-Based Trustworthy AI Testing" not in out and "Assessment Target" not in out
    assert "[+] HTML report:" in out
    print("LOCAL_DEMO_RESULT=" + json.dumps({"mode": mode, "adaptive": adaptive, "observations": len(observations),
          "confirmed_predicates": len(confirmed), "possible": sum(o["classification"] == "POSSIBLE VULNERABILITY" for o in observations),
          "errors": 0, "report": output.name}))
