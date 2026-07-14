from fastapi import APIRouter
from pydantic import BaseModel

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
    # TODO: retrieve relevant cocktail docs + generate answer via RAG pipeline
    answer = f"You asked: {request.question}"
    return AskResponse(answer=answer)