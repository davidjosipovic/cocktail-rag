from app.rag.extraction import extract_entities
from app.rag.generation import generate_answer
from app.rag.retrieval import (
    format_context,
    format_document_context,
    retrieve_documents,
    retrieve_subgraph,
)


def answer_question(question: str) -> str:
    """Run the full RAG pipeline: extract entities, retrieve KG + document context, generate an answer."""
    entities = extract_entities(question)
    kg_contexts = retrieve_subgraph(entities)
    document_contexts = retrieve_documents(question)

    context = (
        "Knowledge Graph Context:\n"
        f"{format_context(kg_contexts)}\n\n"
        "Domain Document Context:\n"
        f"{format_document_context(document_contexts)}"
    )
    return generate_answer(question, context)
