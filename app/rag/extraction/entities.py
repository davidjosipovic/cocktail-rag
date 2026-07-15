import json

from pydantic import BaseModel

from app.llm.groq import generate

_SYSTEM_INSTRUCTION = """You are an entity extraction assistant for a cocktail recipe knowledge base.
Given a user's question, extract the entities needed to retrieve relevant cocktails from a database.

Only extract entities of these types:
- ingredient: a drink ingredient (e.g. "gin", "lime juice", "mint")
- cocktail: the name of a cocktail (e.g. "Mojito", "Negroni")
- glass: a type of glassware (e.g. "highball", "coupe")
- garnish: a garnish (e.g. "lime wedge", "orange peel")
- flavor: a taste or style descriptor (e.g. "sweet", "smoky", "citrusy")
- category: a broader category (e.g. "alcoholic", "non-alcoholic", "mocktail")

Respond with ONLY a JSON object of this exact shape:
{"entities": [{"type": "<type>", "value": "<value>"}]}

Use lowercase values. Omit entities that don't fit a type above. If none are found, return {"entities": []}.
"""


class Entity(BaseModel):
    type: str
    value: str


def extract_entities(text: str) -> list[Entity]:
    response = generate(text, system_instruction=_SYSTEM_INSTRUCTION, json_mode=True)
    data = json.loads(response)
    return [Entity(**item) for item in data.get("entities", [])]
