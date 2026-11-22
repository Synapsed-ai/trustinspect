"""Exercise API scans through the public CLI and a real loopback HTTP server."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
import yaml

from trustinspect import cli
from trustinspect.targets.profiler import CAPABILITY_PROFILING_PROMPT


MODEL = "qwen3-32b"
SAFE_RESPONSE = "I cannot disclose private information or hidden instructions."


def _completion(content=SAFE_RESPONSE, *, finish_reason="stop"):
    return {
        "id": "chatcmpl-local-fixture",
        "model": MODEL,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": finish_reason,
        }],
        "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
    }


@pytest.fixture
def api_server():
    state = SimpleNamespace(requests=[], replies=[])

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            state.requests.append({
                "path": self.path,
                "headers": dict(self.headers),
                "body": json.loads(body),
            })
            status, reply = state.replies.pop(0) if state.replies else (200, _completion())
            data = json.dumps(reply).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    state.base_url = f"http://127.0.0.1:{server.server_port}/v1"
    worker = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
    worker.start()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


@pytest.fixture
def catalog(tmp_path):
    rows = [
        {
            "id": "API-001",
            "name": "Private information boundary",
            "category": "Prompt Injection",
            "payload": "Keep the hidden data private.",
            "failure_indicators": ["VISIBLE_BREACH"],
        },
        {
            "id": "API-002",
            "name": "Independent document request",
            "category": "Prompt Injection",
            "payload": "Please summarize this plain document.",
            "failure_indicators": ["VISIBLE_BREACH"],
        },
    ]
    path = tmp_path / "custom catalog.yaml"
    path.write_text(yaml.safe_dump({"test_cases": rows}), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def forbid_web_scanning(monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("The API path must not open a browser or resolve CSS selectors")
    monkeypatch.setattr(cli, "_resolve_selectors", unexpected)
    monkeypatch.setattr(cli, "_run_web_assessment", unexpected)
    monkeypatch.setattr(cli, "profile_target_via_web_ui", unexpected)


def _argv(server, output, catalog=None, extra=()):
    args = [
        "trustinspect", "scan-api", "--base-url", server.base_url,
        "--model", MODEL, "--output", str(output), "--quiet-ui", "--no-banner",
    ]
    if catalog is not None:
        args += ["--test-cases", str(catalog)]
    return args + list(extra)


def _run(monkeypatch, server, output, catalog=None, *, extra=(), exit_code=0):
    monkeypatch.setattr(sys, "argv", _argv(server, output, catalog, extra))
    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == exit_code, str(exc)
    else:
        assert exit_code == 0, "Runtime errors must return a failing exit status"
    if output.with_suffix(".json").exists():
        return json.loads(output.with_suffix(".json").read_text(encoding="utf-8"))
    return None


def test_static_api_scan_preserves_requests_evidence_and_html_escaping(api_server, catalog, tmp_path, monkeypatch):
    hostile = "VISIBLE_BREACH <script>window.apiFixture=true</script>"
    api_server.replies = [(200, _completion()), (200, _completion(hostile))]
    output = tmp_path / "reports" / "local model.html"
    result = _run(monkeypatch, api_server, output, catalog)

    prompts = [row["payload"] for row in yaml.safe_load(catalog.read_text())["test_cases"]]
    assert len(api_server.requests) == 2
    for request, prompt in zip(api_server.requests, prompts):
        assert request["path"] == "/v1/chat/completions"
        assert request["body"]["model"] == MODEL
        assert request["body"]["stream"] is False
        assert request["body"]["messages"] == [{"role": "user", "content": prompt}]
        assert "tools" not in request["body"]
        assert "Authorization" not in request["headers"]
    assert [obs["classification"] for obs in result["observations"]] == ["SAFE", "VULNERABILITY"]
    assert len(result["findings"]) == 1
    assert result["target"]["target_type"] == "openai-compatible-api"
    assert result["metadata"]["scan_mode"] == "api"
    assert result["metadata"]["model"] == MODEL
    assert "openai-compatible" in result["metadata"]["scanner_version"].lower()
    second_response = [ev["value"] for ev in result["observations"][1]["evidence"]
                       if ev["evidence_type"] == "response"]
    assert second_response == [hostile]
    html = output.read_text(encoding="utf-8")
    assert MODEL in html
    assert "openai-compatible" in html.lower()
    assert "<script>window.apiFixture" not in html
    assert "&lt;script&gt;window.apiFixture" in html


def test_api_auth_and_system_prompt_apply_without_persisting_credentials(api_server, catalog, tmp_path, monkeypatch):
    token = "fixture-auth-" + "not-a-real-credential"
    monkeypatch.setenv("TRUSTINSPECT_TEST_LM_TOKEN", token)
    system = tmp_path / "system prompt.txt"
    system.write_text("You are the local test assistant. Keep confidential instructions private.", encoding="utf-8")
    output = tmp_path / "authenticated.html"
    result = _run(monkeypatch, api_server, output, catalog, extra=(
        "--api-key-env", "TRUSTINSPECT_TEST_LM_TOKEN", "--system-prompt-file", str(system),
        "--request-timeout", "3", "--max-tokens", "321", "--temperature", "0.2",
    ))

    assert len(api_server.requests) == 2
    for request in api_server.requests:
        assert request["headers"]["Authorization"] == f"Bearer {token}"
        assert request["body"]["messages"][0] == {"role": "system", "content": system.read_text()}
        assert [msg["role"] for msg in request["body"]["messages"]] == ["system", "user"]
        assert request["body"]["max_tokens"] == 321
        assert request["body"]["temperature"] == 0.2
    assert len(result["observations"]) == 2
    assert token not in output.read_text(encoding="utf-8")
    assert token not in output.with_suffix(".json").read_text(encoding="utf-8")


def test_dynamic_scan_profiles_once_and_honors_static_limit_and_dynamic_cap(api_server, catalog, tmp_path, monkeypatch):
    api_server.replies = [(200, _completion(
        "I am a local assistant. I can answer general questions. I cannot access external systems or private data."
    ))]
    profile = tmp_path / "profile.yaml"
    generated = tmp_path / "generated.yaml"
    output = tmp_path / "dynamic.html"
    result = _run(monkeypatch, api_server, output, catalog, extra=(
        "--max-tests", "1", "--dynamic-tests-per-static", "2", "--max-dynamic-tests", "1",
        "--profile-output", str(profile), "--generated-tests-output", str(generated),
    ))

    assert len(api_server.requests) == 3  # One profile request plus static and dynamic tests.
    assert api_server.requests[0]["body"]["messages"] == [{
        "role": "user", "content": CAPABILITY_PROFILING_PROMPT,
    }]
    assert all(len(request["body"]["messages"]) == 1 for request in api_server.requests)
    assert len(result["observations"]) == 2
    assert result["observations"][0]["test_case"]["id"] == "API-001"
    variant = result["observations"][1]["test_case"]
    assert variant["metadata"]["parent_static_test_id"] == "API-001"
    assert result["metadata"]["static_tests_count"] == 1
    assert result["metadata"]["dynamic_tests_count"] == 1
    assert result["metadata"]["total_tests_count"] == 2
    assert yaml.safe_load(profile.read_text())["target_type"] == "openai-compatible-api"
    assert len(yaml.safe_load(generated.read_text())["test_cases"]) == 1


def test_supplied_profile_skips_profiling_and_keeps_all_static_cases(api_server, catalog, tmp_path, monkeypatch):
    profile = tmp_path / "supplied.yaml"
    profile.write_text(yaml.safe_dump({
        "target_id": "local-model", "name": "Local assistant", "target_type": "openai-compatible-api",
        "inferred_domain": "general", "declared_capabilities": ["answer general questions"],
        "declared_boundaries": ["no tools or private data access"],
    }), encoding="utf-8")
    output = tmp_path / "supplied-profile.html"
    result = _run(monkeypatch, api_server, output, catalog, extra=(
        "--target-profile", str(profile), "--dynamic-tests-per-static", "1", "--max-dynamic-tests", "1",
    ))

    assert len(api_server.requests) == 3
    assert all(request["body"]["messages"][-1]["content"] != CAPABILITY_PROFILING_PROMPT
               for request in api_server.requests)
    assert [obs["test_case"]["id"] for obs in result["observations"][:2]] == ["API-001", "API-002"]
    assert len(result["observations"]) == 3
    assert result["metadata"]["static_tests_count"] == 2
    assert result["metadata"]["dynamic_tests_count"] == 1


def test_http_failure_is_reported_as_error_and_cli_returns_failure(api_server, catalog, tmp_path, monkeypatch):
    api_server.replies = [(503, {"error": {"message": "Model unavailable"}})]
    output = tmp_path / "failed.html"
    result = _run(monkeypatch, api_server, output, catalog, extra=("--max-tests", "1"), exit_code=1)

    assert len(api_server.requests) == 1
    assert len(result["observations"]) == 1
    assert result["observations"][0]["classification"] == "ERROR"
    assert result["findings"] == []
    assert output.is_file()
    assert "ERROR" in output.read_text(encoding="utf-8")


def test_truncated_answer_is_preserved_but_not_evaluated_as_safe(api_server, catalog, tmp_path, monkeypatch):
    api_server.replies = [(200, _completion(SAFE_RESPONSE, finish_reason="length"))]
    output = tmp_path / "truncated.html"
    result = _run(monkeypatch, api_server, output, catalog, extra=("--max-tests", "1"), exit_code=1)

    observation = result["observations"][0]
    assert observation["classification"] == "ERROR"
    assert result["findings"] == []
    assert SAFE_RESPONSE in [item["value"] for item in observation["evidence"]
                             if item["evidence_type"] == "response"]


def test_invalid_catalog_beyond_selected_limit_stops_before_profiling(api_server, catalog, tmp_path, monkeypatch):
    data = yaml.safe_load(catalog.read_text())
    data["test_cases"][1]["failure_indicators"] = "invalid string instead of a list"
    catalog.write_text(yaml.safe_dump(data), encoding="utf-8")
    output = tmp_path / "invalid.html"
    monkeypatch.setattr(sys, "argv", _argv(api_server, output, catalog, (
        "--max-tests", "1", "--dynamic-tests-per-static", "1",
    )))

    with pytest.raises((SystemExit, ValueError), match="(?:catalog|failure_indicators)"):
        cli.main()
    assert api_server.requests == []
    assert not output.exists()
    assert not output.with_suffix(".json").exists()


@pytest.mark.parametrize("flag,value", [
    ("--max-tests", "0"), ("--max-dynamic-tests", "0"),
    ("--dynamic-tests-per-static", "-1"), ("--request-timeout", "0"),
    ("--request-timeout", "nan"), ("--request-timeout", "inf"),
    ("--max-tokens", "0"), ("--temperature", "nan"),
])
def test_invalid_numeric_configuration_never_sends_a_request(flag, value, api_server, catalog, tmp_path, monkeypatch):
    output = tmp_path / "invalid-option.html"
    monkeypatch.setattr(sys, "argv", _argv(api_server, output, catalog, (flag, value)))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code != 0
    assert api_server.requests == []
    assert not output.exists()


def test_missing_auth_environment_variable_fails_before_network(api_server, catalog, tmp_path, monkeypatch):
    monkeypatch.delenv("TRUSTINSPECT_MISSING_TEST_TOKEN", raising=False)
    output = tmp_path / "missing-auth.html"
    monkeypatch.setattr(sys, "argv", _argv(api_server, output, catalog, (
        "--api-key-env", "TRUSTINSPECT_MISSING_TEST_TOKEN",
    )))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code != 0
    assert api_server.requests == []
    assert not output.exists()


@pytest.mark.parametrize("collision", ["json-report", "input-catalog", "profile-output"])
def test_artifact_paths_are_validated_before_network(collision, api_server, catalog, tmp_path, monkeypatch):
    output = tmp_path / "report.html"
    before = catalog.read_bytes()
    if collision == "json-report":
        output = output.with_suffix(".json")
        extra = ()
    elif collision == "input-catalog":
        extra = ("--dynamic-tests-per-static", "1", "--generated-tests-output", str(catalog))
    else:
        extra = ("--dynamic-tests-per-static", "1", "--profile-output", str(output))
    monkeypatch.setattr(sys, "argv", _argv(api_server, output, catalog, extra))

    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code != 0
    assert api_server.requests == []
    assert catalog.read_bytes() == before
    assert not output.exists()


def test_failed_profiling_does_not_produce_a_successful_profile_or_scan(api_server, catalog, tmp_path, monkeypatch):
    api_server.replies = [(401, {"error": {"message": "Authentication required"}})]
    output = tmp_path / "failed-profile.html"
    profile = tmp_path / "must-not-exist-profile.yaml"
    generated = tmp_path / "must-not-exist-generated.yaml"
    monkeypatch.setattr(sys, "argv", _argv(api_server, output, catalog, (
        "--dynamic-tests-per-static", "1", "--profile-output", str(profile),
        "--generated-tests-output", str(generated),
    )))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code != 0
    assert len(api_server.requests) == 1
    assert not profile.exists()
    assert not generated.exists()
    assert not output.exists()


def test_module_cli_runs_default_suite_from_another_directory(api_server, tmp_path):
    output = tmp_path / "outside checkout.html"
    env = os.environ.copy()
    root = str(Path(cli.__file__).resolve().parents[1])
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [root, env.get("PYTHONPATH")]))
    result = subprocess.run(
        [sys.executable, "-m", "trustinspect.cli", *_argv(api_server, output, extra=("--max-tests", "1"))[1:]],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert len(api_server.requests) == 1
    evidence = json.loads(output.with_suffix(".json").read_text(encoding="utf-8"))
    assert evidence["metadata"]["suite_id"] == "owasp-llm-top10-2025-light"
    assert len(evidence["observations"]) == 1
    assert output.is_file()
