"""
Parametrized tests for parse_tokens_from_rules_text().

Test cases are loaded from fixtures/token_test_cases.json. Each entry specifies:
  - id: unique test identifier
  - description: human-readable explanation
  - card_name: the card whose rules text is being parsed
  - rules: the rules text to feed into the parser
  - expected_specialized: list of token dicts that should appear in the first return value
  - expected_common: list of common token names that should appear in the second return value

Run with:
    pytest tests/test_token_discovery/ -v
"""

import json
import os
import pytest

from src.token_generation.token_parser import parse_tokens_from_rules_text


# ---------------------------------------------------------------------------
# Load test data
# ---------------------------------------------------------------------------

_FIXTURES_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "token_test_cases.json")

with open(_FIXTURES_PATH) as _f:
    TEST_CASES = json.load(_f)


# ---------------------------------------------------------------------------
# Parametrized test
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", TEST_CASES, ids=[c["id"] for c in TEST_CASES])
def test_token_discovery(case, mock_common_tokens):
    """Each case exercises one rules-text snippet and checks the parser output."""
    specialized, common = parse_tokens_from_rules_text(
        case["rules"],
        card_name=case.get("card_name", ""),
        common_tokens_list=mock_common_tokens,
    )

    # --- check specialized tokens ---
    expected_specialized = case.get("expected_specialized", [])
    for expected in expected_specialized:
        match = next((t for t in specialized if t["name"] == expected["name"]), None)
        assert match is not None, (
            f"[{case['id']}] Expected specialized token '{expected['name']}' not found. "
            f"Got: {[t['name'] for t in specialized]}"
        )
        for field, value in expected.items():
            assert match.get(field) == value, (
                f"[{case['id']}] Token '{expected['name']}' field '{field}': "
                f"expected {value!r}, got {match.get(field)!r}"
            )
    assert len(specialized) == len(expected_specialized), (
        f"[{case['id']}] Wrong number of specialized tokens: "
        f"expected {len(expected_specialized)}, got {len(specialized)}. "
        f"Tokens: {[t['name'] for t in specialized]}"
    )

    # --- check common tokens ---
    expected_common = case.get("expected_common", [])
    assert sorted(common) == sorted(expected_common), (
        f"[{case['id']}] Common tokens mismatch: "
        f"expected {sorted(expected_common)}, got {sorted(common)}"
    )
