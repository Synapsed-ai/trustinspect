"""Direct, stateless Chat Completions transport for local and compatible models.

The client sends text only. It never executes tool calls, follows redirects,
uses environment proxies, retries prompts, or reuses conversation history.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from http.client import HTTPException
import json
import math
import socket
import time
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from trustinspect.analyzers.heuristic import HeuristicTrustAnalyzer
from trustinspect.core.models import (
    Classification,
    EvidenceItem,
    EvidenceType,
    Observation,
    Target,
    TestCase,
)
from trustinspect.scanners.base import ScannerAdapter


SCANNER_VERSION = "openai-compatible-http v0.1"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class ChatCompletion:
    content: str
    metadata: dict[str, Any]


class APIClientError(RuntimeError):
    """A safe diagnostic, optionally retaining incomplete textual evidence."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: int | None = None,
        partial_content: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.partial_content = partial_content
        self.metadata = dict(metadata or {})


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _normalize_base_url(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Base URL must be an HTTP(S) URL, for example http://127.0.0.1:1234/v1.")
    value = value.strip()
    if not value.isascii():
        raise ValueError("Base URL must use an ASCII host name and percent-encoded paths.")
    if any(ord(char) < 33 or ord(char) == 127 for char in value):
        raise ValueError("Base URL must not contain whitespace or control characters.")
    try:
        parsed = urlsplit(value)
        port = parsed.port  # Validate malformed and out-of-range ports now.
        hostname = parsed.hostname
    except ValueError:
        raise ValueError("Base URL has an invalid host or port.") from None
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise ValueError("Base URL must use http:// or https:// and include a host.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Base URL must not contain credentials; configure an API key separately.")
    if parsed.query or parsed.fragment or "?" in value or "#" in value:
        raise ValueError("Base URL must not contain a query string or fragment.")
    if "\\" in parsed.netloc or "%" in parsed.netloc:
        raise ValueError("Base URL has an invalid host.")
    if port == 0:
        raise ValueError("Base URL port must be between 1 and 65535.")
    path = parsed.path.rstrip("/")
    if not path:
        path = "/v1"
    elif path.endswith("/chat/completions"):
        raise ValueError("Use the API base URL ending in /v1, without /chat/completions.")
    elif path == "/api/v1" or not path.endswith("/v1"):
        raise ValueError("Use the OpenAI-compatible base URL ending in /v1, for example http://127.0.0.1:1234/v1.")
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def _finite_number(name: str, value: Any, *, minimum: float, maximum: float | None = None) -> float:
    try:
        finite = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"{name} must be a finite number.")
    number = float(value)
    if number < minimum or (maximum is not None and number > maximum):
        if maximum is None:
            raise ValueError(f"{name} must be greater than {minimum}.")
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return number


class OpenAICompatibleClient:
    """A small OpenAI-compatible, non-streaming HTTP client with safe evidence."""

    def __init__(
        self,
        *,
        model: str,
        base_url: str = "http://127.0.0.1:1234/v1",
        timeout: float = 180.0,
        max_tokens: int = 2048,
        temperature: float = 0.6,
        api_key: str | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self.base_url = _normalize_base_url(base_url)
        self.endpoint = self.base_url + "/chat/completions"
        if not isinstance(model, str) or not model.strip() or any(ord(c) < 32 or ord(c) == 127 for c in model):
            raise ValueError("Model must be a non-empty API model identifier without control characters.")
        self.model = model.strip()
        self.timeout = _finite_number("Timeout", timeout, minimum=0.0, maximum=86400.0)
        if self.timeout == 0:
            raise ValueError("Timeout must be greater than zero.")
        if type(max_tokens) is not int or not 0 < max_tokens <= 2147483647:
            raise ValueError("max_tokens must be a positive integer no greater than 2147483647.")
        self.max_tokens = max_tokens
        self.temperature = _finite_number("Temperature", temperature, minimum=0.0, maximum=2.0)
        if api_key is not None and (
            not isinstance(api_key, str) or any(ord(c) < 32 or ord(c) == 127 or ord(c) > 255 for c in api_key)
        ):
            raise ValueError("API key must be text without control characters and valid as an HTTP header.")
        if system_prompt is not None and not isinstance(system_prompt, str):
            raise ValueError("System prompt must be text.")
        self._api_key = api_key or None
        self.system_prompt = system_prompt
        # Local inference must not accidentally traverse HTTP(S)_PROXY. A
        # redirect could otherwise forward a bearer token to a different host.
        self._opener = build_opener(ProxyHandler({}), _NoRedirects())

    def redact(self, value: Any) -> Any:
        """Remove the configured authentication token from persisted evidence."""
        if isinstance(value, str):
            return value.replace(self._api_key, "[REDACTED]") if self._api_key else value
        if isinstance(value, dict):
            return {self.redact(key): self.redact(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.redact(item) for item in value]
        return value

    def complete(self, prompt: str) -> ChatCompletion:
        """Return final text or raise APIClientError; each call starts fresh."""
        started = time.monotonic()
        metadata: dict[str, Any] = {
            "transport": "openai-compatible-http",
            "method": "POST",
            "endpoint": self.endpoint,
            "requested_model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout,
            "timeout_kind": "network_operation",
            "conversation_mode": "independent",
            "stream": False,
            "system_prompt_present": self.system_prompt is not None,
        }
        if self.system_prompt is not None:
            metadata["system_prompt"] = self.system_prompt
        try:
            if not isinstance(prompt, str) or not prompt.strip():
                raise APIClientError("invalid_prompt", "Prompt must be non-empty text.")
            messages: list[dict[str, str]] = []
            if self.system_prompt is not None:
                messages.append({"role": "system", "content": self.system_prompt})
            messages.append({"role": "user", "content": prompt})
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if self._api_key:
                headers["Authorization"] = "Bearer " + self._api_key
            request = Request(self.endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            try:
                with self._opener.open(request, timeout=self.timeout) as response:
                    metadata["http_status"] = response.status
                    body = response.read(MAX_RESPONSE_BYTES + 1)
            except HTTPError as exc:
                status = exc.code
                exc.close()
                metadata["http_status"] = status
                if 300 <= status < 400:
                    raise APIClientError("redirect_refused", "API redirect refused. Use the server's final OpenAI-compatible base URL.", status=status) from None
                if status in {401, 403}:
                    message = f"API authentication failed (HTTP {status}). Check the server authentication setting and API key."
                elif status == 404:
                    message = "Chat Completions endpoint not found (HTTP 404). Check the server address and /v1 base URL."
                else:
                    message = f"API request failed (HTTP {status}). Check the model server logs."
                raise APIClientError("http_error", message, status=status) from None
            except (TimeoutError, socket.timeout):
                raise APIClientError("timeout", "API network operation timed out. Check the model server or increase --request-timeout.") from None
            except URLError as exc:
                if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                    raise APIClientError("timeout", "API network operation timed out. Check the model server or increase --request-timeout.") from None
                raise APIClientError("connection_error", "Could not reach the model API. Start the server and check its address and port.") from None
            except (OSError, HTTPException):
                raise APIClientError("connection_error", "The model API connection failed before a complete response was received.") from None
            if len(body) > MAX_RESPONSE_BYTES:
                raise APIClientError("response_too_large", "API response exceeded the response-size limit; it was not evaluated.")
            try:
                data = json.loads(body.decode("utf-8"), parse_constant=_reject_json_constant)
            except (ValueError, UnicodeError, RecursionError):
                raise APIClientError("invalid_json", "The API did not return valid JSON for Chat Completions.") from None
            content = self._parse_completion(data, metadata)
        except APIClientError as exc:
            metadata.update(exc.metadata)
            metadata["duration_seconds"] = round(time.monotonic() - started, 3)
            metadata["error_code"] = exc.code
            raise APIClientError(
                exc.code,
                self.redact(str(exc)),
                status=exc.status if exc.status is not None else metadata.get("http_status"),
                partial_content=self.redact(exc.partial_content),
                metadata=self.redact(metadata),
            ) from None
        metadata["duration_seconds"] = round(time.monotonic() - started, 3)
        return ChatCompletion(content=self.redact(content), metadata=self.redact(metadata))

    @staticmethod
    def _parse_completion(data: Any, metadata: dict[str, Any]) -> str:
        if not isinstance(data, dict):
            raise APIClientError("invalid_response", "The Chat Completions response must be a JSON object.")
        if "error" in data and data["error"] is not None:
            raise APIClientError("api_error", "The model API returned an error object. Check the model server logs.")
        for source, destination in (("id", "response_id"), ("model", "returned_model")):
            if isinstance(data.get(source), str):
                metadata[destination] = data[source][:1024]
        usage = data.get("usage")
        if isinstance(usage, dict):
            metadata["usage"] = {
                key: usage[key] for key in ("prompt_tokens", "completion_tokens", "total_tokens")
                if type(usage.get(key)) is int and usage[key] >= 0
            }
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise APIClientError("invalid_response", "The API response has no valid completion choice.")
        choice = choices[0]
        message = choice.get("message")
        if not isinstance(message, dict) or message.get("role", "assistant") != "assistant":
            raise APIClientError("invalid_response", "The API response has no valid assistant message.")
        reason = choice.get("finish_reason")
        if isinstance(reason, str):
            metadata["finish_reason"] = reason[:128]
        reasoning = [message[key] for key in ("reasoning_content", "reasoning", "thinking") if message.get(key) is not None]
        if any(not isinstance(value, str) for value in reasoning):
            raise APIClientError("invalid_response", "The API reasoning field has an unsupported format.")
        metadata["reasoning_present"] = any(bool(value) for value in reasoning)
        if reasoning:
            metadata["reasoning_format"] = "separate_field"
            metadata["reasoning_characters"] = sum(len(value) for value in reasoning)
        content = _text_content(message.get("content"))
        refusal = message.get("refusal")
        if not content.strip() and isinstance(refusal, str) and refusal.strip():
            content = refusal
            metadata["response_source"] = "refusal"
        else:
            metadata["response_source"] = "content"
            if not reasoning:
                content = _final_answer_from_inline_reasoning(content, metadata)
        if message.get("tool_calls") or message.get("function_call") or (isinstance(reason, str) and reason in {"tool_calls", "function_call"}):
            metadata["tool_calls_executed"] = False
            raise APIClientError("unsupported_tool_call", "The API requested a tool/function call. No tools were executed and this response was not evaluated.", partial_content=content)
        if reason == "length":
            raise APIClientError("truncated_response", "The API response reached its token limit. Increase --max-tokens and rerun; partial text was not evaluated.", partial_content=content)
        if reason == "content_filter":
            raise APIClientError("filtered_response", "The API marked this completion as filtered; model behavior could not be evaluated.", partial_content=content)
        if reason != "stop":
            raise APIClientError("incomplete_response", "The API did not confirm a complete assistant answer (finish_reason must be 'stop').", partial_content=content)
        if not content.strip():
            raise APIClientError("empty_response", "The API returned no final answer text. Reasoning alone is not evaluated; check the model and token limit.")
        return content


def _reject_json_constant(value: str) -> None:
    raise ValueError("Non-finite JSON number")


def _text_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for part in value:
            if not isinstance(part, dict) or not isinstance(part.get("type"), str) or part["type"] not in {"text", "output_text"} or not isinstance(part.get("text"), str):
                raise APIClientError("unsupported_content", "The API returned an unsupported non-text content part.", partial_content="\n".join(parts))
            parts.append(part["text"])
        return "\n".join(parts)
    raise APIClientError("invalid_response", "The API assistant content must be text or text content parts.")


def _final_answer_from_inline_reasoning(content: str, metadata: dict[str, Any]) -> str:
    """Separate a protocol prefix, never remove arbitrary tags from an answer.

    Qwen documents a leading <think> block followed by the final answer; its
    prompt template can also consume the opening marker. LM Studio can instead
    supply a separate reasoning_content field, in which case this parser is
    deliberately bypassed. Unframed/unfinished markers are not safe to score.
    Sources: https://huggingface.co/Qwen/Qwen3-32B
    https://lmstudio.ai/blog/lmstudio-v0.3.9
    """
    stripped = content.lstrip()
    if "<think>" not in content and "</think>" not in content:
        return content
    metadata["raw_response_content"] = content
    if stripped.startswith("<think>"):
        thought, delimiter, final = stripped[len("<think>"):].partition("</think>")
        metadata["reasoning_present"] = True
        metadata["reasoning_format"] = "initial_think_block"
        metadata["reasoning_characters"] = len(thought)
        if not delimiter:
            raise APIClientError("incomplete_reasoning", "The model stopped inside its thinking block without a final answer. Check the model and token limit.")
        if "<think>" in thought or final.lstrip().startswith(("<think>", "</think>")):
            raise APIClientError("ambiguous_reasoning", "The API returned ambiguous thinking markers. Enable separate reasoning output in the model server before evaluating this response.", partial_content=content)
        metadata["response_source"] = "content_after_think_block"
        return final.lstrip()
    if stripped.startswith("</think>"):
        final = stripped[len("</think>"):].lstrip()
        if final.startswith(("<think>", "</think>")):
            raise APIClientError("ambiguous_reasoning", "The API returned ambiguous thinking markers. Enable separate reasoning output in the model server before evaluating this response.", partial_content=content)
        metadata["reasoning_format"] = "leading_think_close"
        metadata["response_source"] = "content_after_think_block"
        return final
    # With no opening marker, prose before </think> could be reasoning or a
    # literal example. Preserve it for review instead of silently discarding it.
    raise APIClientError("ambiguous_reasoning", "The API mixes text with unframed thinking markers. Enable separate reasoning output in the model server before evaluating this response.", partial_content=content)


class OpenAICompatibleScanner(ScannerAdapter):
    SCANNER_VERSION = SCANNER_VERSION

    def __init__(
        self,
        *,
        client: OpenAICompatibleClient,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        analyzer: HeuristicTrustAnalyzer | None = None,
    ) -> None:
        self.client = client
        self.progress_callback = progress_callback
        self.analyzer = analyzer or HeuristicTrustAnalyzer()

    def _emit(self, event: dict[str, Any]) -> None:
        if self.progress_callback:
            try:
                self.progress_callback(self.client.redact(event))
            except Exception:
                pass  # Terminal presentation must not interrupt evidence collection.

    def run(self, target: Target, test_cases: Iterable[TestCase]) -> list[Observation]:
        cases = list(test_cases)
        observations: list[Observation] = []
        self._emit({"event": "run_started", "total": len(cases), "target": target.name, "url": self.client.endpoint})
        try:
            for index, test_case in enumerate(cases, 1):
                details = {
                    "index": index,
                    "total": len(cases),
                    "test_id": test_case.id,
                    "test_name": test_case.name,
                    "category": test_case.category,
                    "source": test_case.metadata.get("source") or "static",
                    "parent_static_test_id": test_case.metadata.get("parent_static_test_id") or "",
                    "aitg_layer": test_case.metadata.get("aitg_layer") or "",
                    "prompt": test_case.payload,
                }
                self._emit({"type": "test_start", "event": "test_started", **details})
                observation = self._run_single(target, test_case, index)
                observations.append(observation)
                response = next((item.value for item in observation.evidence if item.evidence_type == EvidenceType.RESPONSE), "")
                self._emit({
                    "type": "test_result", "event": "test_completed", **details,
                    "response": response or observation.rationale,
                    "classification": observation.classification.value,
                    "confidence": observation.confidence,
                    "rationale": observation.rationale,
                    "duration_seconds": observation.metadata.get("duration_seconds"),
                })
        finally:
            self._emit({"event": "run_completed", "total": len(cases)})
        return observations

    def _run_single(self, target: Target, test_case: TestCase, index: int) -> Observation:
        evidence = [EvidenceItem(
            id=f"ev-api-{index}-prompt", evidence_type=EvidenceType.PROMPT,
            value=self.client.redact(test_case.payload),
        )]
        try:
            completion = self.client.complete(test_case.payload)
            metadata = completion.metadata
            content = completion.content
            classification, confidence, rationale = self.analyzer.analyze(test_case, content)
            if classification == Classification.ERROR and rationale.startswith("Output capture guard:"):
                rationale = rationale.replace(
                    "Recalibrate the output selector before evaluating model behavior.",
                    "The API answer resembles the submitted prompt; check the model server response before evaluating model behavior.",
                )
            evidence.append(EvidenceItem(id=f"ev-api-{index}-response", evidence_type=EvidenceType.RESPONSE, value=content))
        except APIClientError as exc:
            metadata = exc.metadata
            classification, confidence, rationale = Classification.ERROR, 0.0, str(exc)
            if exc.partial_content:
                evidence.append(EvidenceItem(
                    id=f"ev-api-{index}-response", evidence_type=EvidenceType.RESPONSE,
                    value=exc.partial_content, metadata={"partial": True, "evaluated": False},
                ))
            evidence.append(EvidenceItem(id=f"ev-api-{index}-error", evidence_type=EvidenceType.LOG, value=str(exc)))
        evidence.append(EvidenceItem(
            id=f"ev-api-{index}-http", evidence_type=EvidenceType.HTTP_TRACE,
            value=self.client.redact(metadata),
        ))
        return Observation(
            id=f"obs-api-{index}",
            target=replace(target, **self.client.redact(asdict(target))),
            test_case=replace(test_case, **self.client.redact(asdict(test_case))),
            classification=classification,
            confidence=confidence,
            evidence=evidence,
            analyzer=self.analyzer.ANALYZER_VERSION,
            rationale=self.client.redact(rationale),
            metadata={"scanner": self.SCANNER_VERSION, **self.client.redact(metadata)},
        )
