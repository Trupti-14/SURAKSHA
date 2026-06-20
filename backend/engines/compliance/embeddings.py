import hashlib
import math
import re


TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{1,}")


def _tokens(text: str) -> list[str]:
    return TOKEN_PATTERN.findall((text or "").lower())


def embed_text(text: str, dimensions: int = 128) -> list[float]:
    """Return a deterministic local embedding using hashed token features."""
    if dimensions <= 0:
        raise ValueError("dimensions must be positive")

    vector = [0.0] * dimensions
    tokens = _tokens(text)

    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        weight = 1.0 + min(len(token), 12) / 24.0
        vector[index] += sign * weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector

    return [value / norm for value in vector]


def embed_documents(texts: list[str], dimensions: int = 128) -> list[list[float]]:
    return [embed_text(text, dimensions=dimensions) for text in texts]
