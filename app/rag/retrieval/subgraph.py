import re
from collections import defaultdict
from dataclasses import dataclass, field

from app.db.graphdb import query_data
from app.rag.extraction import Entity

_ONTOLOGY = "https://example.org/cocktail-rag/ontology/"
_COCKTAIL_CLASS = _ONTOLOGY + "Cocktail"

# Maps an extracted entity type to the predicate linking a Cocktail to it.
# This dataset has no separate Garnish class - garnishes (e.g. "lemon peel")
# are modeled as Ingredient nodes, so extraction treats them as "ingredient" too.
_ENTITY_PREDICATES = {
    "ingredient": _ONTOLOGY + "hasIngredient",
    "glass": _ONTOLOGY + "servedIn",
    "category": _ONTOLOGY + "hasCategory",
    "country": _ONTOLOGY + "hasOrigin",
}

_PREDICATE_FIELDS = {
    _ONTOLOGY + "servedIn": "glass",
    _ONTOLOGY + "hasOrigin": "origin",
    _ONTOLOGY + "hasCategory": "category",
}


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _local_name(iri: str) -> str:
    return iri.rsplit("/", 1)[-1].replace("-", " ")


@dataclass
class CocktailContext:
    name: str
    glass: str | None = None
    origin: str | None = None
    category: str | None = None
    ingredients: list[str] = field(default_factory=list)


def _boundary_regex_filter(var: str, slugs: list[str]) -> str:
    # Anchor to "/" or "-" boundaries so e.g. "gin" doesn't match "ginger-ale".
    alternatives = [f'REGEX(STR({var}), "(^|[-/]){slug}($|[-/])", "i")' for slug in slugs]
    return "(" + " || ".join(alternatives) + ")"


def _find_cocktail_iris(entities: list[Entity]) -> list[str]:
    # Group by extracted type: values within a type are alternatives (OR),
    # e.g. "gin" or "vodka"; different types must all be satisfied (AND),
    # e.g. ingredient=gin and glass=highball.
    groups: dict[str, list[str]] = defaultdict(list)
    for entity in entities:
        # _slugify strips everything but [a-z0-9-], so this is safe to inline into SPARQL.
        slug = _slugify(entity.value)
        if slug:
            groups[entity.type].append(slug)

    triples = [f"?cocktail a <{_COCKTAIL_CLASS}> ."]
    filters = []
    for index, (entity_type, slugs) in enumerate(groups.items()):
        if entity_type == "cocktail":
            filters.append(_boundary_regex_filter("?cocktail", slugs))
        elif entity_type in _ENTITY_PREDICATES:
            var = f"?match{index}"
            triples.append(f"?cocktail <{_ENTITY_PREDICATES[entity_type]}> {var} .")
            filters.append(_boundary_regex_filter(var, slugs))

    if not filters:
        return []

    query = (
        "SELECT DISTINCT ?cocktail WHERE { "
        + " ".join(triples)
        + " FILTER(" + " && ".join(filters) + ") }"
    )
    return [str(row[0]) for row in query_data(query)]


def _fetch_cocktails(cocktail_iris: list[str]) -> list[CocktailContext]:
    if not cocktail_iris:
        return []

    values = " ".join(f"<{iri}>" for iri in cocktail_iris)
    query = f"""
        SELECT ?cocktail ?p ?o WHERE {{
            VALUES ?cocktail {{ {values} }}
            ?cocktail ?p ?o .
        }}
    """

    contexts: dict[str, CocktailContext] = {}
    for cocktail, predicate, obj in query_data(query):
        iri = str(cocktail)
        ctx = contexts.setdefault(iri, CocktailContext(name=_local_name(iri)))

        predicate = str(predicate)
        if predicate == _ENTITY_PREDICATES["ingredient"]:
            ctx.ingredients.append(_local_name(str(obj)))
        elif predicate in _PREDICATE_FIELDS:
            setattr(ctx, _PREDICATE_FIELDS[predicate], _local_name(str(obj)))

    return list(contexts.values())


def retrieve_subgraph(entities: list[Entity]) -> list[CocktailContext]:
    """Resolve extracted entities to matching cocktails and fetch their full subgraph."""
    cocktail_iris = _find_cocktail_iris(entities)
    return _fetch_cocktails(cocktail_iris)


def format_context(contexts: list[CocktailContext]) -> str:
    """Render retrieved cocktail subgraphs as text ready for the generation layer's prompt."""
    if not contexts:
        return "No matching cocktails found."

    blocks = []
    for ctx in contexts:
        lines = [f"Cocktail: {ctx.name}"]
        if ctx.category:
            lines.append(f"Category: {ctx.category}")
        if ctx.glass:
            lines.append(f"Served in: {ctx.glass}")
        if ctx.origin:
            lines.append(f"Origin: {ctx.origin}")
        if ctx.ingredients:
            lines.append(f"Ingredients: {', '.join(ctx.ingredients)}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)
