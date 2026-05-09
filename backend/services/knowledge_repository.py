from dataclasses import dataclass
from math import log, sqrt
import re
from pathlib import Path


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+", re.UNICODE)
STOPWORDS = {
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
    "that",
    "the",
    "this",
    "to",
    "with",
}


@dataclass
class KnowledgeChunk:
    title: str
    summary: str
    quote: str | None = None
    keywords: list[str] | None = None
    temperament: str | None = None
    source: str | None = None
    source_type: str | None = None

    def text(self) -> str:
        parts = [
            self.title,
            self.summary,
            self.quote or "",
            " ".join(self.keywords or []),
            self.temperament or "",
            self.source or "",
            self.source_type or "",
        ]
        return " ".join(parts)


def _tokens(value: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(value) if token.lower() not in STOPWORDS]


def _term_frequency(tokens: list[str]) -> dict[str, float]:
    counts: dict[str, float] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0.0) + 1.0
    total = float(len(tokens) or 1)
    return {token: count / total for token, count in counts.items()}


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    numerator = sum(weight * right.get(token, 0.0) for token, weight in left.items())
    left_norm = sqrt(sum(weight * weight for weight in left.values()))
    right_norm = sqrt(sum(weight * weight for weight in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def load_knowledge(path: Path) -> list[KnowledgeChunk]:
    if not path.exists():
        return []

    raw_chunks = [chunk.strip() for chunk in path.read_text(encoding="utf-8").split("\n\n") if chunk.strip()]
    chunks: list[KnowledgeChunk] = []

    for raw in raw_chunks:
        fields: dict[str, str] = {}
        for line in raw.splitlines():
            key, sep, value = line.partition(":")
            if sep:
                fields[key.strip().lower()] = value.strip()

        title = fields.get("title") or raw.splitlines()[0][:80]
        summary = fields.get("summary") or raw
        keywords = [item.strip() for item in fields.get("keywords", "").split(",") if item.strip()]
        chunks.append(
            KnowledgeChunk(
                title=title,
                summary=summary,
                quote=fields.get("quote"),
                keywords=keywords,
                temperament=fields.get("khí") or fields.get("khi"),
                source=fields.get("source"),
                source_type=fields.get("source type") or fields.get("source_type"),
            )
        )

    return chunks


def retrieve(query: str, chunks: list[KnowledgeChunk], limit: int = 4) -> list[tuple[KnowledgeChunk, float]]:
    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    documents = [_tokens(chunk.text()) for chunk in chunks]
    document_count = len(documents) or 1
    document_frequency: dict[str, int] = {}
    for tokens in documents:
        for token in set(tokens):
            document_frequency[token] = document_frequency.get(token, 0) + 1

    def vector(tokens: list[str]) -> dict[str, float]:
        tf = _term_frequency(tokens)
        return {
            token: frequency * (log((1 + document_count) / (1 + document_frequency.get(token, 0))) + 1.0)
            for token, frequency in tf.items()
        }

    query_vector = vector(query_tokens)
    ranked: list[tuple[KnowledgeChunk, float]] = []
    for chunk, tokens in zip(chunks, documents, strict=False):
        chunk_vector = vector(tokens)
        semantic_score = _cosine(query_vector, chunk_vector)
        keyword_bonus = sum(0.08 for keyword in chunk.keywords or [] if keyword.lower() in query.lower())
        title_bonus = 0.05 if chunk.title.lower() in query.lower() else 0.0
        score = semantic_score + keyword_bonus + title_bonus
        if score > 0:
            ranked.append((chunk, score))

    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:limit]
