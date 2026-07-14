# cocktail-rag

A simple RAG (Retrieval-Augmented Generation) application for cocktail recipes, built with FastAPI and backed by a GraphDB (SPARQL) knowledge graph.

## Prerequisites

- Python 3.14
- Access to a running GraphDB instance and repository (or another SPARQL 1.1-compatible endpoint)

## Getting started

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd cocktail-rag
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Copy the example file and fill in your GraphDB connection details:

   ```bash
   cp .env.example .env
   ```

   `.env` requires:

   | Variable | Description |
   |---|---|
   | `GRAPHDB_HOST` | Base URL of the GraphDB instance |
   | `GRAPHDB_REPOSITORY` | Name of the repository to query |
   | `GRAPHDB_USERNAME` | GraphDB username |
   | `GRAPHDB_PASSWORD` | GraphDB password |

5. **Run the server**

   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://127.0.0.1:8000`, with interactive docs at `http://127.0.0.1:8000/docs`.

## API endpoints

### `GET /`

Health check. Returns:

```json
{ "status": "ok" }
```

### `POST /ask`

Main RAG entry point. Accepts a question and returns a generated answer.

Request body:

```json
{ "question": "What cocktails can I make with gin and lime?" }
```

Response:

```json
{ "answer": "..." }
```

Currently a stub — it echoes the question back (`app/api/routes.py`). This is where the retrieval step described below should be wired in.

### `GET /db-check`

Verifies connectivity to GraphDB by running a trivial SPARQL query (`SELECT * WHERE { ?s ?p ?o } LIMIT 1`). Returns `{"status": "connected", "sample_row_count": <n>}` on success, or a `503` with an error detail if the connection fails.

## Using the GraphDB connection in the RAG pipeline

Database access lives in [app/db/graphdb.py](app/db/graphdb.py), which wraps an `rdflib` `SPARQLUpdateStore` pointed at the repository configured in `.env` (loaded via [app/core/config.py](app/core/config.py)). It exposes two functions:

- `query_data(query: str)` — runs a SPARQL `SELECT`/`ASK`/`CONSTRUCT` query and returns the results.
- `update_data(query: str)` — runs a SPARQL `INSERT`/`DELETE` update and commits it.

To implement retrieval inside `POST /ask`, import `query_data` in `app/api/routes.py` and use it to fetch relevant triples before generating the answer:

```python
from app.db.graphdb import query_data

@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    sparql = """
        SELECT ?cocktail ?ingredient WHERE {
            ?cocktail a :Cocktail ;
                      :hasIngredient ?ingredient .
            FILTER(CONTAINS(LCASE(STR(?ingredient)), "gin"))
        }
        LIMIT 10
    """
    context_rows = list(query_data(sparql))

    # Feed context_rows into the LLM prompt to generate a grounded answer
    answer = generate_answer(request.question, context_rows)
    return AskResponse(answer=answer)
```

In practice, the question text should first be parsed (e.g. keyword/entity extraction) to build a targeted SPARQL query, the returned triples formatted as context, and that context passed to the LLM generation step alongside the original question.
