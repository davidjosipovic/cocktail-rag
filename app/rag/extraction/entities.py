import json
from functools import lru_cache

from pydantic import BaseModel

from app.db.graphdb import query_data
from app.llm.groq import generate

_ONTOLOGY = "https://example.org/cocktail-rag/ontology/"

# These are small, closed vocabularies in the knowledge graph, so the LLM is
# grounded against the real values instead of inventing its own wording
# (e.g. "party drinks" vs. the DB's "punch party drink").
_CONTROLLED_TYPES = {
    "glass": "GlassType",
    "category": "Category",
    "country": "Country",
}

_BASE_INSTRUCTION = """You are an entity extraction assistant for a cocktail recipe knowledge base.
Given a user's question, extract the entities needed to retrieve relevant cocktails from a database.

Only extract entities of these types:
- ingredient: a drink ingredient or garnish (e.g. "gin", "lime juice", "mint", "orange peel")
- cocktail: the name of a cocktail (e.g. "Mojito", "Negroni")
- flavor: a taste or style descriptor (e.g. "sweet", "smoky", "citrusy")
- glass: a type of glassware. Must be one of: {glass_values}
- category: a broader drink category. Must be one of: {category_values}
- country: a country of origin. Must be one of: {country_values}

Respond with ONLY a JSON object of this exact shape:
{{"entities": [{{"type": "<type>", "value": "<value>"}}]}}

Use lowercase values. Omit entities that don't fit a type above. For glass/category/country, only
output a value if it is an exact match (or unambiguous synonym) from its allowed list above - never
pick the closest allowed value as a fallback. For example, "non-alcoholic" or "mocktail" has no match
in category's allowed list, so no category entity should be output for it.

If the question is not about cocktails, drinks, or bartending, return {{"entities": []}} even if it
happens to mention a word that appears in an allowed list (e.g. a country name) - matching a country,
glass, or category name is not enough on its own; it must be asked about in a drink-related sense.
"""


def _local_name(iri: str) -> str:
    return iri.rsplit("/", 1)[-1].replace("-", " ")


@lru_cache(maxsize=1)
def _controlled_vocab() -> dict[str, list[str]]:
    vocab = {}
    for entity_type, class_name in _CONTROLLED_TYPES.items():
        query = f"SELECT DISTINCT ?s WHERE {{ ?s a <{_ONTOLOGY}{class_name}> }}"
        vocab[entity_type] = sorted(_local_name(str(row[0])) for row in query_data(query))
    return vocab


def _system_instruction() -> str:
    vocab = _controlled_vocab()
    return _BASE_INSTRUCTION.format(
        glass_values=", ".join(vocab["glass"]),
        category_values=", ".join(vocab["category"]),
        country_values=", ".join(vocab["country"]),
    )


class Entity(BaseModel):
    type: str
    value: str


def extract_entities(text: str) -> list[Entity]:
    response = generate(text, system_instruction=_system_instruction(), json_mode=True)
    data = json.loads(response)
    return [Entity(**item) for item in data.get("entities", [])]
