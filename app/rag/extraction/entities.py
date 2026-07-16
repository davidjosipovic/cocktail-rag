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

Only extract a value that is stated or clearly implied by the question's own wording. Never use outside
knowledge to fill in a value the question does not mention, even if you are confident you know the
real-world answer - the database may disagree with real-world facts, and a guessed filter will hide the
correct match. This applies to every type (country, glass, category, ingredient), not just the examples
below. A question that asks the database to tell you an attribute is not the same as a question that
already states that attribute:
- "Where was the Bloody Mary created?" -> only {{"type": "cocktail", "value": "bloody mary"}}
  (do NOT add a country entity - the country is what's being asked for)
- "What glass is a Negroni served in?" -> only {{"type": "cocktail", "value": "negroni"}}
  (do NOT add a glass entity)
- "What category is a Martini?" -> only {{"type": "cocktail", "value": "martini"}}
  (do NOT add a category entity)
- "What cocktails are served in a highball glass?" -> {{"type": "glass", "value": "highball glass"}}
  (here the glass IS stated by the question, as the filter being searched on, so it is extracted)
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
