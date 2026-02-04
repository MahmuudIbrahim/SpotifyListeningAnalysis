from __future__ import annotations

import re
from typing import Optional

_SECTION_RE = re.compile(r"\[.*?\]")  # [Chorus], [Verse 1], etc.
_EMBED_RE = re.compile(r"\bEmbed\b", re.IGNORECASE)


def contains_cjk(text: str) -> bool:
    return any(
        '\u4e00' <= ch <= '\u9fff' or  # CJK Unified
        '\u3040' <= ch <= '\u30ff' or  # Hiragana/Katakana
        '\uac00' <= ch <= '\ud7af'     # Hangul
        for ch in text
    )


def clean_lyrics(text: Optional[str]) -> Optional[str]:
    if not text:
        return None

    t = text
    t = _SECTION_RE.sub(" ", t)
    # Remove metadata lines
    t = re.sub(r"(Produced by|Written by|Release Date).*?$", " ", t, flags=re.IGNORECASE | re.MULTILINE)
    t = _EMBED_RE.sub(" ", t)

    # Remove common trailing garbage like "You might also like"
    t = re.sub(r"You might also like.*$", " ", t, flags=re.IGNORECASE | re.DOTALL)

    # Normalize whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t if t else None
