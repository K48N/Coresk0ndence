from __future__ import annotations

import re
from html import unescape


_WHITESPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://\S+")
_TAG_RE = re.compile(r"<[^>]+>")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = unescape(text)
    text = text.replace("\xa0", " ")
    text = _TAG_RE.sub(" ", text)
    text = _URL_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def trim_word_boundary(text: str, max_chars: int) -> str:
    text = clean_text(text)
    if max_chars <= 0 or not text:
        return ""
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]

    window = text[: max_chars + 1]
    cut = window.rfind(" ")
    if cut < int(max_chars * 0.6):
        cut = max_chars
    return window[:cut].rstrip(" ,;:-") + "..."


def trim_sentence_boundary(text: str, max_chars: int, min_chars: int = 80) -> str:
    text = clean_text(text)
    if max_chars <= 0 or not text:
        return ""
    if len(text) <= max_chars:
        return text

    parts = _SENTENCE_RE.split(text)
    picked: list[str] = []
    used = 0

    for part in parts:
        part = part.strip()
        if not part:
            continue

        extra = len(part) + (1 if picked else 0)
        if used + extra > max_chars:
            break

        picked.append(part)
        used += extra

    if picked and used >= min(min_chars, max_chars):
        out = " ".join(picked).strip()
        if out.endswith((".", "!", "?", "...")):
            return out
        return out + "."

    return trim_word_boundary(text, max_chars)