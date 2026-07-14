from fastapi import FastAPI
from app.api.routes import router

app=FastAPI(title="Cocktail RAG", description="A simple RAG application for cocktail recipes", version="1.0.0")

app.include_router(router)