from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.rag.extraction import Entity
    from app.rag.retrieval.documents import DocumentContext
    from app.rag.retrieval.subgraph import CocktailContext

__all__ = [
    "CocktailContext",
    "DocumentContext",
    "format_context",
    "format_document_context",
    "retrieve_documents",
    "retrieve_subgraph",
]


def retrieve_documents(query: str, top_k: int = 3) -> list[DocumentContext]:
    from app.rag.retrieval.documents import retrieve_documents as _retrieve_documents

    return _retrieve_documents(query, top_k=top_k)


def format_document_context(contexts: list[DocumentContext]) -> str:
    from app.rag.retrieval.documents import format_document_context as _format_document_context

    return _format_document_context(contexts)


def retrieve_subgraph(entities: list[Entity]) -> list[CocktailContext]:
    from app.rag.retrieval.subgraph import retrieve_subgraph as _retrieve_subgraph

    return _retrieve_subgraph(entities)


def format_context(contexts: list[CocktailContext]) -> str:
    from app.rag.retrieval.subgraph import format_context as _format_context

    return _format_context(contexts)


def __getattr__(name: str) -> Any:
    if name == "DocumentContext":
        from app.rag.retrieval.documents import DocumentContext

        return DocumentContext
    if name == "CocktailContext":
        from app.rag.retrieval.subgraph import CocktailContext

        return CocktailContext
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
