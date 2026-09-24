"""Supported predicate names shared by catalog validation and runtime analysis."""
SUPPORTED_MATCH_TYPES = frozenset({
    "contains", "contains_anywhere", "contains_unquoted", "ends_with",
    "ends_with_unquoted", "exact", "exact_match", "regex",
    "disclosure_claim", "specific_internal_claim", "claims_access",
    "claims_completion", "unsafe_echo", "output_length_over",
})

# These signals alone do not establish actual disclosure, side effects or script execution.
REVIEW_ONLY_MATCH_TYPES = frozenset({
    "disclosure_claim", "specific_internal_claim", "claims_access",
    "claims_completion", "unsafe_echo",
})
