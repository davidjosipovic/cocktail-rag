from app.dc.domain_corpus import (
    DocumentContext,
    format_document_context,
    retrieve_domain_documents,
)


def retrieve_documents(query: str, top_k: int = 3) -> list[DocumentContext]:
    """Retrieve the most similar local corpus documents for a user query."""
    return retrieve_domain_documents(query, top_k=top_k)