"""Parsers for LeetCode-style input strings."""

from __future__ import annotations

import ast
import io
import re
import tokenize
from typing import Any

from src.execution.models import ListNode, TreeNode


def _normalize_js_tokens(text: str) -> str:
    """Safely replace JavaScript literals (null, true, false) with Python equivalents (None, True, False)."""
    try:
        tokens = []
        for tok in tokenize.tokenize(io.BytesIO(text.encode("utf-8")).readline):
            if tok.type == tokenize.NAME:
                if tok.string == "null":
                    tokens.append((tok.type, "None"))
                    continue
                elif tok.string == "true":
                    tokens.append((tok.type, "True"))
                    continue
                elif tok.string == "false":
                    tokens.append((tok.type, "False"))
                    continue
            tokens.append((tok.type, tok.string))
        return tokenize.untokenize(tokens).decode("utf-8")
    except Exception:
        # Fallback to regex word boundary
        s = re.sub(r"\bnull\b", "None", text)
        s = re.sub(r"\btrue\b", "True", s)
        return re.sub(r"\bfalse\b", "False", s)


def parse_leetcode_inputs(raw_text: str) -> dict[str, Any]:
    """Parse LeetCode problem input specifications into native Python objects.

    Examples:
        - "head = [1, 2, 3, 4, 5]" -> {"head": ListNode(1, ...)}
        - "root = [3, 9, 20, null, null, 15, 7]" -> {"root": TreeNode(3, ...)}
        - "nums = [2, 7, 11, 15], target = 9" -> {"nums": [2, 7, 11, 15], "target": 9}
        - "[10, 20, 30]" or "10, 20, 30" -> {"nums": [10, 20, 30]}

    Returns:
        Dictionary mapping variable names to parsed Python objects.

    Raises:
        ValueError: If input syntax cannot be parsed.
    """
    text = raw_text.strip()
    if not text:
        return {}

    normalized = _normalize_js_tokens(text)

    # Split into declaration segments: handles newlines and comma-separated declarations (e.g. a = 1, b = 2)
    segments: list[str] = []
    for line in normalized.splitlines():
        line = line.strip()
        if not line:
            continue
        # Split on commas that precede variable assignments (e.g. "x = [1,2], y = 3")
        parts = re.split(r",\s*(?=[a-zA-Z_]\w*\s*=)", line)
        for part in parts:
            if part.strip():
                segments.append(part.strip())

    results: dict[str, Any] = {}

    for segment in segments:
        if "=" in segment:
            var_part, val_part = segment.split("=", 1)
            var_name = var_part.strip()
            val_str = val_part.strip()

            try:
                evaluated_val = ast.literal_eval(val_str)
            except Exception as exc:
                raise ValueError(f"Could not parse value for '{var_name}': {val_str}. Details: {exc}")

            # Smart conversion based on parameter name
            var_lower = var_name.lower()
            if var_lower in ("head", "list", "node") and isinstance(evaluated_val, (list, tuple)):
                results[var_name] = ListNode.from_list(list(evaluated_val))
            elif var_lower in ("root", "tree") and isinstance(evaluated_val, (list, tuple)):
                results[var_name] = TreeNode.from_level_order(list(evaluated_val))
            elif isinstance(evaluated_val, tuple):
                results[var_name] = list(evaluated_val)
            else:
                results[var_name] = evaluated_val

        else:
            # Unnamed parameter (e.g. "[1, 2, 3]" or "1, 2, 3" or '"hello"')
            try:
                val = ast.literal_eval(segment)
            except Exception:
                # Try wrapping in brackets if it's comma-separated numbers (e.g. "1, 2, 3")
                try:
                    val = ast.literal_eval(f"[{segment}]")
                except Exception as exc:
                    raise ValueError(f"Could not parse input expression: '{segment}'. Details: {exc}")

            if isinstance(val, str):
                results["s"] = val
            elif isinstance(val, (list, tuple)):
                results["nums"] = list(val)
            else:
                results["arg0"] = val

    return results
