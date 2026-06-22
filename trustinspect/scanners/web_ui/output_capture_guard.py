from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from html import unescape
import re
from typing import Iterable, Sequence


_WHITESPACE_RE = re.compile(r"\s+")
_WORD_RE = re.compile(r"[a-zA-Z0-9_]+")


@dataclass(frozen=True)
class EchoCheckResult:
    is_echo: bool
    reason: str
    score: float


def normalize_for_capture_guard(value: str | None) -> str:
    """Normalize text for prompt/response echo comparison.

    The guard intentionally ignores HTML escaping, whitespace differences and
    case. It is used to detect output selectors that accidentally capture the
    user-message bubble instead of the assistant response.
    """
    text = unescape(value or "")
    text = text.replace("\u00a0", " ")
    text = _WHITESPACE_RE.sub(" ", text).strip().lower()
    return text


def _tokens(value: str) -> list[str]:
    return [t for t in _WORD_RE.findall(value.lower()) if len(t) > 2]


def _token_recall(prompt: str, response: str) -> float:
    prompt_tokens = _tokens(prompt)
    if not prompt_tokens:
        return 0.0
    response_token_set = set(_tokens(response))
    if not response_token_set:
        return 0.0
    hits = sum(1 for token in prompt_tokens if token in response_token_set)
    return hits / max(len(prompt_tokens), 1)


def check_prompt_echo(
    prompt: str | None,
    response: str | None,
    *,
    exact_min_len: int = 8,
    near_duplicate_threshold: float = 0.92,
    containment_min_len: int = 80,
    token_recall_threshold: float = 0.92,
) -> EchoCheckResult:
    """Return whether a captured response is likely just the submitted prompt.

    This protects TrustInspect from false positives caused by overly broad
    output selectors such as selectors that match both user and assistant
    bubbles. It is conservative: genuine assistant responses that merely mention
    parts of the prompt should not be flagged unless they are near-duplicates of
    the whole submitted prompt.
    """
    raw_prompt = prompt or ""
    raw_response = response or ""
    p = normalize_for_capture_guard(raw_prompt)
    r = normalize_for_capture_guard(raw_response)

    if not p or not r:
        return EchoCheckResult(False, "prompt or response is empty", 0.0)

    if len(p) >= exact_min_len and p == r:
        return EchoCheckResult(
            True,
            "captured response is exactly equal to the submitted prompt",
            1.0,
        )

    # If a long prompt is contained almost entirely in the response and the
    # response does not add much, the selector likely captured a message bubble
    # or conversation container containing the user prompt.
    if len(p) >= containment_min_len and p in r:
        prompt_fraction = len(p) / max(len(r), 1)
        if prompt_fraction >= 0.70:
            return EchoCheckResult(
                True,
                "captured response contains the submitted prompt almost verbatim",
                round(prompt_fraction, 3),
            )

    ratio = SequenceMatcher(None, p, r).ratio()
    length_ratio = min(len(p), len(r)) / max(len(p), len(r), 1)
    if ratio >= near_duplicate_threshold and length_ratio >= 0.70:
        return EchoCheckResult(
            True,
            "captured response is a near-duplicate of the submitted prompt",
            round(ratio, 3),
        )

    # Token recall catches cases where line wrapping or DOM splitting changes
    # punctuation but still captures essentially the prompt. Keep it restricted
    # to long prompts to avoid false positives on short challenge responses.
    if len(p) >= containment_min_len:
        recall = _token_recall(p, r)
        if recall >= token_recall_threshold and length_ratio >= 0.65:
            return EchoCheckResult(
                True,
                "captured response has very high token overlap with the submitted prompt",
                round(recall, 3),
            )

    return EchoCheckResult(False, "captured response is not a prompt echo", round(ratio, 3))


def is_prompt_echo(prompt: str | None, response: str | None) -> tuple[bool, str, float]:
    """Compatibility wrapper used by scanner/analyzer code."""
    result = check_prompt_echo(prompt, response)
    return result.is_echo, result.reason, result.score


def filter_prompt_echo_candidates(
    prompt: str | None,
    candidates: Sequence[str] | Iterable[str],
) -> list[str]:
    """Return candidates that do not look like the submitted prompt."""
    kept: list[str] = []
    for candidate in candidates:
        is_echo, _, _ = is_prompt_echo(prompt, candidate)
        if not is_echo:
            kept.append(candidate)
    return kept


def format_prompt_echo_error(
    prompt: str | None,
    response: str | None,
    *,
    input_selector: str | None = None,
    output_selector: str | None = None,
) -> str:
    result = check_prompt_echo(prompt, response)
    selector_note = ""
    if input_selector or output_selector:
        selector_note = f" input_selector={input_selector!r}; output_selector={output_selector!r}."
    return (
        "Output capture appears to be the submitted user prompt rather than the assistant response. "
        f"Reason: {result.reason}; score={result.score}.{selector_note} "
        "This usually means the output selector matches user-message bubbles or a mixed conversation container. "
        "Recalibrate the output selector and choose a selector that captures only assistant responses."
    )
