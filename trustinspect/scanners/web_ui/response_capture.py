"""Attribute output nodes to a submitted turn before judging their content.

This module is browser-independent so capture behavior can be tested without
network access or a browser driver. A quiet interval is a completion heuristic,
not a protocol-level end-of-stream signal. Configure a target-specific busy
selector where the application exposes one.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import math
import re

from trustinspect.core.output_capture_guard import is_prompt_echo


@dataclass(frozen=True)
class OutputNode:
    key: str
    text: str


_PENDING = re.compile(
    r"^(?:thinking|typing|loading|generating(?: response)?|processing|please wait)"
    r"(?:\s*(?:\.{1,3}|…))?\s*$", re.IGNORECASE,
)


class ResponseTracker:
    """Require a new/updated terminal output and a sustained quiet interval.

    Existing historical nodes are never selected just because their text is
    different from the previous final response. Identical replies on distinct
    new nodes are valid. Replaced DOM nodes with unchanged historical text are
    matched positionally to avoid treating a redraw as a fresh answer.
    """

    def __init__(self, baseline: Sequence[OutputNode], prompt: str, stable_for: float = 1.0):
        if not math.isfinite(stable_for) or stable_for <= 0:
            raise ValueError("stable_for must be a finite positive number")
        self.baseline = tuple(baseline)
        self.prompt = prompt
        self.stable_for = stable_for
        self._baseline_by_key = {n.key: n.text for n in self.baseline}
        self._candidate: tuple[str, str] | None = None
        self._stable_since: float | None = None

    def _fresh(self, nodes: Sequence[OutputNode]) -> list[OutputNode]:
        # A newly appended message may be textually identical to the previous
        # one. Prefix comparison also accommodates full DOM re-rendering.
        prefix_preserved = len(nodes) >= len(self.baseline) and all(
            new.text == old.text for old, new in zip(self.baseline, nodes)
        )
        if prefix_preserved:
            return list(nodes[len(self.baseline):])

        fresh = []
        baseline_keys = set(self._baseline_by_key)
        anchor_positions = [index for index, node in enumerate(nodes) if node.key in baseline_keys]
        last_baseline_key = self.baseline[-1].key if self.baseline else None
        if not anchor_positions:
            # Complete redraw: only an unchanged history prefix followed by an
            # updated final output is attributable without surviving identities.
            if (self.baseline and len(nodes) == len(self.baseline)
                    and all(new.text == old.text for old, new in zip(self.baseline[:-1], nodes[:-1]))
                    and nodes[-1].text != self.baseline[-1].text):
                return [nodes[-1]]
            return []
        last_anchor = max(anchor_positions)
        for index, node in enumerate(nodes):
            if node.key not in baseline_keys and index > last_anchor:
                fresh.append(node)
            elif node.key == last_baseline_key and node.text != self._baseline_by_key[node.key]:
                # Single-output UIs may update the same node for each turn.
                fresh.append(node)
        return fresh

    def observe(self, nodes: Sequence[OutputNode], now: float, *, busy: bool = False) -> str | None:
        candidates = self._fresh(nodes)
        # Inspect only the newest attributable output, never fall back to an
        # earlier message while the newest one is empty, pending, or ambiguous.
        candidate = candidates[-1] if candidates else None
        text = candidate.text.strip() if candidate else ""
        if (not text or busy or _PENDING.fullmatch(text)
                or is_prompt_echo(self.prompt, text)[0]):
            self._candidate = None
            self._stable_since = None
            return None
        identity = (candidate.key, text)
        if identity != self._candidate:
            self._candidate = identity
            self._stable_since = now
            return None
        if self._stable_since is not None and now - self._stable_since >= self.stable_for:
            return text
        return None
