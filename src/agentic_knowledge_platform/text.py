from __future__ import annotations

import hashlib
import re
from collections import Counter

STOP_WORDS = {
    "的",
    "了",
    "和",
    "是",
    "在",
    "与",
    "到",
    "及",
    "并",
    "对",
    "将",
    "把",
    "可",
    "会",
    "为",
    "on",
    "the",
    "and",
    "for",
    "with",
    "to",
    "a",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    latin_tokens = re.findall(r"[a-z0-9_]+", lowered)
    han_chars = [char for char in lowered if "\u4e00" <= char <= "\u9fff"]
    han_bigrams = [f"{han_chars[index]}{han_chars[index + 1]}" for index in range(len(han_chars) - 1)]
    tokens = latin_tokens + han_bigrams + han_chars
    return [token for token in tokens if token and token not in STOP_WORDS]


def sentence_split(text: str) -> list[str]:
    compact = text.replace("\r", "\n")
    sentences = re.split(r"(?<=[。！？.!?])\s+|\n+", compact)
    return [normalize_text(sentence) for sentence in sentences if normalize_text(sentence)]


def top_keywords(text: str, limit: int = 8) -> list[str]:
    counter = Counter(tokenize(text))
    return [token for token, _ in counter.most_common(limit)]


def estimate_tokens(text: str) -> int:
    return max(1, len(tokenize(text)))


def short_snippet(text: str, limit: int = 140) -> str:
    compact = normalize_text(text)
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def slugify(text: str) -> str:
    lowered = text.lower()
    ascii_only = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    if ascii_only:
        return ascii_only
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
