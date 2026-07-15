from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


CORPUS_DIR = Path(__file__).resolve().parent / "corpus"
DEFAULT_TOP_K = 3
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")
_STOPWORDS = {
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
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
}


@dataclass(frozen=True)
class CorpusDocument:
    doc_id: str
    title: str
    path: Path
    text: str


@dataclass(frozen=True)
class DocumentContext:
    rank: int
    score: float
    doc_id: str
    title: str
    path: str
    text: str


class DomainCorpusIndex:
    """Small in-memory TF-IDF index for the local cocktail domain corpus."""

    def __init__(self, documents: list[CorpusDocument]):
        self.documents = documents
        self._idf: dict[str, float] = {}
        self._vectors: list[dict[str, float]] = []
        self._build()

    @classmethod
    def from_corpus_dir(cls, corpus_dir: Path = CORPUS_DIR) -> DomainCorpusIndex:
        return cls(load_corpus_documents(corpus_dir))

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[DocumentContext]:
        if top_k <= 0:
            return []

        query_vector = self._vectorize(_tokenize(query))
        if not query_vector:
            return []

        scored: list[tuple[float, int]] = []
        for index, document_vector in enumerate(self._vectors):
            score = _dot(query_vector, document_vector)
            if score > 0:
                scored.append((score, index))

        scored.sort(key=lambda item: item[0], reverse=True)
        results: list[DocumentContext] = []
        for rank, (score, index) in enumerate(scored[:top_k], start=1):
            document = self.documents[index]
            results.append(
                DocumentContext(
                    rank=rank,
                    score=score,
                    doc_id=document.doc_id,
                    title=document.title,
                    path=str(document.path),
                    text=document.text,
                )
            )
        return results

    def _build(self) -> None:
        tokenized_documents = [_tokenize(f"{doc.title}\n{doc.text}") for doc in self.documents]
        document_count = len(tokenized_documents)
        document_frequency: Counter[str] = Counter()
        for tokens in tokenized_documents:
            document_frequency.update(set(tokens))

        self._idf = {
            token: math.log((1 + document_count) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }
        self._vectors = [self._vectorize(tokens) for tokens in tokenized_documents]

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        counts = Counter(token for token in tokens if token in self._idf)
        if not counts:
            return {}

        vector = {
            token: (1 + math.log(count)) * self._idf[token]
            for token, count in counts.items()
        }
        norm = math.sqrt(sum(weight * weight for weight in vector.values()))
        if norm == 0:
            return {}
        return {token: weight / norm for token, weight in vector.items()}


_INDEX_CACHE: dict[Path, DomainCorpusIndex] = {}


def load_corpus_documents(corpus_dir: Path = CORPUS_DIR) -> list[CorpusDocument]:
    corpus_dir = Path(corpus_dir)
    documents: list[CorpusDocument] = []
    for path in sorted(corpus_dir.glob("*.txt")):
        text = _normalize_whitespace(path.read_text(encoding="utf-8"))
        if not text:
            continue
        documents.append(
            CorpusDocument(
                doc_id=path.stem,
                title=_extract_title(text, path.stem),
                path=path,
                text=text,
            )
        )
    return documents


def get_domain_corpus_index(
    corpus_dir: Path = CORPUS_DIR,
    force_rebuild: bool = False,
) -> DomainCorpusIndex:
    cache_key = Path(corpus_dir).resolve()
    if force_rebuild or cache_key not in _INDEX_CACHE:
        _INDEX_CACHE[cache_key] = DomainCorpusIndex.from_corpus_dir(cache_key)
    return _INDEX_CACHE[cache_key]


def retrieve_domain_documents(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    corpus_dir: Path = CORPUS_DIR,
) -> list[DocumentContext]:
    return get_domain_corpus_index(corpus_dir).retrieve(query, top_k=top_k)


def format_document_context(contexts: list[DocumentContext]) -> str:
    if not contexts:
        return "No matching domain documents found."

    blocks = []
    for context in contexts:
        blocks.append(
            "\n".join(
                [
                    f"Document: {context.title}",
                    f"Source: {context.doc_id}",
                    f"Similarity: {context.score:.3f}",
                    context.text,
                ]
            )
        )
    return "\n\n".join(blocks)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text.strip())


def _extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return fallback.replace("-", " ").title()


def _tokenize(text: str) -> list[str]:
    return [
        token
        for token in _TOKEN_PATTERN.findall(text.lower())
        if token not in _STOPWORDS and len(token) > 1
    ]


def _dot(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(weight * right.get(token, 0.0) for token, weight in left.items())