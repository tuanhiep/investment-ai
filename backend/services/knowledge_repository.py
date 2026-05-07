from dataclasses import dataclass
import re
from pathlib import Path


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+", re.UNICODE)


@dataclass
class KnowledgeChunk:
    title: str
    summary: str
    quote: str | None = None
    keywords: list[str] | None = None
    temperament: str | None = None

    def text(self) -> str:
        parts = [self.title, self.summary, self.quote or "", " ".join(self.keywords or []), self.temperament or ""]
        return " ".join(parts)


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(value)}


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
            )
        )

    return chunks


def retrieve(query: str, chunks: list[KnowledgeChunk], limit: int = 4) -> list[tuple[KnowledgeChunk, float]]:
    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    ranked: list[tuple[KnowledgeChunk, float]] = []
    for chunk in chunks:
        chunk_tokens = _tokens(chunk.text())
        overlap = query_tokens & chunk_tokens
        keyword_bonus = sum(1 for keyword in chunk.keywords or [] if keyword.lower() in query.lower())
        score = len(overlap) + keyword_bonus * 1.5
        if score > 0:
            ranked.append((chunk, score))

    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:limit]
