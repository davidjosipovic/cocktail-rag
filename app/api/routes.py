from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from app.db.graphdb import query_data
from app.llm.groq import generate

router=APIRouter()

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str

@router.get("/")
def health():
    return {"status": "ok"}

@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    # TODO: retrieve relevant cocktail docs from GraphDB before generating an answer
    answer = generate(request.question)
    return AskResponse(answer=answer)

@router.get("/db-check")
def db_check():
    try:
        results = query_data("SELECT * WHERE { ?s ?p ?o } LIMIT 1")
        rows = list(results)
        return {"status": "connected", "sample_row_count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"GraphDB connection failed: {e}")

