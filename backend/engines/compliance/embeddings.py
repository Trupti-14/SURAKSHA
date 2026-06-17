"""Offline text normalization and similarity helpers for compliance records."""

from __future__ import annotations

from collections import Counter
import math
import re
import unicodedata


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def normalize_text(text: str | None) -> str:
    """Return lowercase ASCII text with punctuation collapsed to spaces."""

    if not text:
        return ""

    normalized = unicodedata.normalize("NFKD", str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    lowercase = ascii_text.lower()
    return " ".join(TOKEN_PATTERN.findall(lowercase))


def tokenize(text: str | None) -> list[str]:
    """Tokenize text into meaningful lowercase terms."""

    normalized = normalize_text(text)
    if not normalized:
        return []

    return [
        token
        for token in normalized.split()
        if len(token) > 1 and token not in STOP_WORDS
    ]


def embed_text(text: str | None) -> dict[str, float]:
    """Create a simple bag-of-words term-frequency embedding."""

    tokens = tokenize(text)
    if not tokens:
        return {}

    counts = Counter(tokens)
    total = float(sum(counts.values()))
    return {token: count / total for token, count in counts.items()}


def cosine_similarity(
    first_embedding: dict[str, float] | None,
    second_embedding: dict[str, float] | None,
) -> float:
    """Return cosine similarity for two sparse embedding dictionaries."""

    if not first_embedding or not second_embedding:
        return 0.0

    shared_terms = set(first_embedding) & set(second_embedding)
    dot_product = sum(
        first_embedding[term] * second_embedding[term] for term in shared_terms
    )
    first_norm = math.sqrt(sum(value * value for value in first_embedding.values()))
    second_norm = math.sqrt(sum(value * value for value in second_embedding.values()))

    if first_norm == 0.0 or second_norm == 0.0:
        return 0.0

    return dot_product / (first_norm * second_norm)


def keyword_overlap(first_text: str | None, second_text: str | None) -> float:
    """Return keyword overlap as a 0-1 Jaccard score."""

    first_terms = set(tokenize(first_text))
    second_terms = set(tokenize(second_text))
    if not first_terms or not second_terms:
        return 0.0

    return len(first_terms & second_terms) / len(first_terms | second_terms)
