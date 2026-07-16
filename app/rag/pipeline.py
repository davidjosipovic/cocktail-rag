from app.rag.extraction import extract_entities
from app.rag.generation import generate_answer
from app.rag.retrieval import format_context, retrieve_subgraph


def answer_question(question: str) -> str:
    """Run the full RAG pipeline: extract entities, retrieve context, generate an answer."""
    entities = extract_entities(question)
    contexts = retrieve_subgraph(entities)
    context = format_context(contexts)
    return generate_answer(question, context)
