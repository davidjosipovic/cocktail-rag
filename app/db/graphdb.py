from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

from app.core.config import settings

_query_endpoint = f"{settings.graphdb_host}/repositories/{settings.graphdb_repository}"
_update_endpoint = f"{_query_endpoint}/statements"

store = SPARQLUpdateStore(
    query_endpoint=_query_endpoint,
    update_endpoint=_update_endpoint,
    auth=(settings.graphdb_username, settings.graphdb_password),
    autocommit=False,
)


def query_data(query: str):
    return store.query(query)


def update_data(query: str):
    result = store.update(query)
    store.commit()
    return result
