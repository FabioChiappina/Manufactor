"""
Token detection and generation from card rules text.

Automatically parses card rules text to identify and generate token cards
that are created by card abilities.
"""

from src.token_generation.token_parser import parse_tokens_from_rules_text

__all__ = ['parse_tokens_from_rules_text']
