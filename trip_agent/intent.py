from __future__ import annotations
import re
from typing import Callable

Extractor = Callable[[str], dict]

WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}

def _num(tok: str) -> int | None:
    return int(tok) if tok.isdigit() else WORDS.get(tok.lower())

def rule_extractor(text: str) -> dict:
    """Deterministic baseline extractor. In production a second, model-based extractor runs alongside."""
    out: dict = {}
    t = text.lower()
    if m := re.search(r"\b(\w+)\s+nights?\b", t):
        if (n := _num(m.group(1))) is not None:
            out["nights"] = n
    if m := re.search(r"\b(?:for|with)\s+(\w+)\s+(?:people|adults|travellers|of us)\b", t):
        if (n := _num(m.group(1))) is not None:
            out["travellers"] = n
    if m := re.search(r"\b(?:to|in|visit)\s+([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)?)", text):
        out["destination"] = m.group(1)
    return out

def consensus(text: str, a: Extractor, b: Extractor) -> tuple[dict, list[str]]:
    """Keep only slots both extractors agree on; report disagreements so the agent asks instead of guessing."""
    ra, rb = a(text), b(text)
    agreed = {k: v for k, v in ra.items() if rb.get(k) == v}
    conflicts = sorted(k for k in set(ra) | set(rb) if k in ra and k in rb and ra[k] != rb[k])
    # a slot only one extractor found is accepted (no contradiction), conflicts are dropped
    for src, other in ((ra, rb), (rb, ra)):
        for k, v in src.items():
            if k not in other:
                agreed.setdefault(k, v)
    return agreed, conflicts
