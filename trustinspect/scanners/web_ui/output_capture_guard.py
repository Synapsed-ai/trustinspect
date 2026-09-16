"""Backward-compatible imports for the canonical core capture guard."""
from trustinspect.core.output_capture_guard import (
    EchoCheckResult, check_prompt_echo, filter_prompt_echo_candidates,
    format_prompt_echo_error, is_prompt_echo, normalize_for_capture_guard,
)

__all__ = [
    "EchoCheckResult", "check_prompt_echo", "filter_prompt_echo_candidates",
    "format_prompt_echo_error", "is_prompt_echo", "normalize_for_capture_guard",
]
