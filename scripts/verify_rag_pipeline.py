"""
Manual verification of the extraction -> retrieval pipeline against the live
GraphDB instance. Not a test suite - just run it directly:

    python3 scripts/verify_rag_pipeline.py
"""

import sys

sys.path.insert(0, ".")

from app.rag.extraction import Entity, extract_entities
from app.rag.retrieval import format_context, retrieve_subgraph

failures = []


def check_retrieval(name: str, entities: list[Entity], expected: set[str]) -> None:
    result = {c.name for c in retrieve_subgraph(entities)}
    if result == expected:
        print(f"OK   {name}")
    else:
        failures.append(name)
        print(f"FAIL {name}\n     expected: {sorted(expected)}\n     got:      {sorted(result)}")


def check(name: str, condition: bool) -> None:
    if condition:
        print(f"OK   {name}")
    else:
        failures.append(name)
        print(f"FAIL {name}")


print("--- retrieval (deterministic, no LLM) ---")

check_retrieval(
    "ingredient=gin",
    [Entity(type="ingredient", value="gin")],
    {"negroni", "martini", "long island iced tea"},
)
check_retrieval(
    "ingredient=rum matches only rum, not unrelated cocktails",
    [Entity(type="ingredient", value="rum")],
    {"daiquiri", "pina colada", "cuba libre", "mojito", "long island iced tea", "mai tai", "dark and stormy"},
)
check_retrieval(
    "boundary regex: 'gin' must not match 'ginger ale' / 'ginger beer'",
    [Entity(type="ingredient", value="gin")],
    {"negroni", "martini", "long island iced tea"},
)
check_retrieval(
    "boundary regex: 'ice' must not match '*-juice' ingredients",
    [Entity(type="ingredient", value="ice")],
    {"manhattan"},
)
check_retrieval(
    "ingredient=lime juice is narrower than ingredient=lime",
    [Entity(type="ingredient", value="lime juice")],
    {"margarita", "moscow mule", "cosmopolitan"},
)
check_retrieval(
    "garnish-like ingredient (lemon peel) resolves via ingredient type",
    [Entity(type="ingredient", value="lemon peel")],
    {"long island iced tea"},
)
check_retrieval(
    "cocktail=negroni matches by name",
    [Entity(type="cocktail", value="negroni")],
    {"negroni"},
)
check_retrieval(
    "OR within same type: ingredient=gin OR ingredient=vodka",
    [Entity(type="ingredient", value="gin"), Entity(type="ingredient", value="vodka")],
    {"negroni", "martini", "moscow mule", "sex on the beach", "bloody mary", "long island iced tea", "blue lagoon"},
)
check_retrieval(
    "AND across types: ingredient=(lime OR tequila) AND glass=highball glass",
    [
        Entity(type="ingredient", value="lime"),
        Entity(type="ingredient", value="tequila"),
        Entity(type="glass", value="highball glass"),
    ],
    {"cuba libre", "mojito", "long island iced tea"},
)
check_retrieval(
    "AND across types: country=italy AND glass=old fashioned glass",
    [Entity(type="country", value="italy"), Entity(type="glass", value="old fashioned glass")],
    {"negroni"},
)
check_retrieval(
    "category=punch party drink",
    [Entity(type="category", value="punch party drink")],
    {"moscow mule"},
)
check_retrieval("unknown ingredient matches nothing", [Entity(type="ingredient", value="unicorn tears")], set())
check_retrieval("empty entity list matches nothing", [], set())

check("format_context on empty list returns a clear message", format_context([]) == "No matching cocktails found.")
check(
    "format_context on a match includes the cocktail name and its ingredients",
    "Cocktail: negroni" in (text := format_context(retrieve_subgraph([Entity(type="cocktail", value="negroni")])))
    and "gin" in text,
)

print("\n--- extraction + retrieval smoke test (uses the real LLM, non-deterministic) ---")

smoke_questions = [
    "What cocktails can I make with gin?",
    "How do I make a Negroni?",
    "What is the capital of France?",
    "What cocktails are from Italy served in an old fashioned glass?",
]
for question in smoke_questions:
    entities = extract_entities(question)
    contexts = retrieve_subgraph(entities)
    print(f"\nQ: {question}\n entities: {entities}\n matched: {[c.name for c in contexts]}")

check(
    "off-domain question extracts no entities",
    extract_entities("What is the capital of France?") == [],
)
check(
    "'gin' question extracts an ingredient=gin entity",
    any(e.type == "ingredient" and e.value == "gin" for e in extract_entities("What cocktails use gin?")),
)
check(
    "named-cocktail question extracts a cocktail entity",
    any(e.type == "cocktail" for e in extract_entities("How do I make a Negroni?")),
)

print(f"\n{'ALL CHECKS PASSED' if not failures else f'{len(failures)} CHECK(S) FAILED: ' + ', '.join(failures)}")
sys.exit(1 if failures else 0)
