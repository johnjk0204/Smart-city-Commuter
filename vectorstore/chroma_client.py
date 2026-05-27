import logging
from typing import Any, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

COLLECTION_ROUTES = "city_routes"
COLLECTION_LANDMARKS = "landmarks"
COLLECTION_TRANSIT = "transit_stops"
COLLECTION_TRAFFIC = "traffic_patterns"


class ChromaVectorStore:
    """ChromaDB client for semantic retrieval of commute knowledge."""

    def __init__(self, persist_dir: str = "./chroma_db"):
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collections: dict[str, Any] = {}
        logger.info("ChromaDB initialized at: %s", persist_dir)

    def get_or_create_collection(self, name: str):
        if name not in self._collections:
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[name]

    def upsert(self, collection_name: str, documents: list[str], ids: list[str], metadatas: Optional[list[dict]] = None):
        col = self.get_or_create_collection(collection_name)
        col.upsert(documents=documents, ids=ids, metadatas=metadatas or [{} for _ in ids])
        logger.debug("Upserted %d docs into '%s'", len(documents), collection_name)

    def query(self, collection_name: str, query_text: str, n_results: int = 5) -> list[dict]:
        col = self.get_or_create_collection(collection_name)
        count = col.count()
        if count == 0:
            return []
        n_results = min(n_results, count)
        results = col.query(query_texts=[query_text], n_results=n_results)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        return [
            {"document": doc, "metadata": meta, "score": 1 - dist}
            for doc, meta, dist in zip(docs, metas, distances)
        ]

    def search_routes(self, query: str, n: int = 3) -> list[dict]:
        return self.query(COLLECTION_ROUTES, query, n)

    def search_landmarks(self, query: str, n: int = 3) -> list[dict]:
        return self.query(COLLECTION_LANDMARKS, query, n)

    def search_transit(self, query: str, n: int = 3) -> list[dict]:
        return self.query(COLLECTION_TRANSIT, query, n)

    def search_traffic(self, query: str, n: int = 3) -> list[dict]:
        return self.query(COLLECTION_TRAFFIC, query, n)

    def collection_count(self, name: str) -> int:
        try:
            return self.get_or_create_collection(name).count()
        except Exception:
            return 0

    def is_seeded(self) -> bool:
        return all(
            self.collection_count(c) > 0
            for c in [COLLECTION_ROUTES, COLLECTION_LANDMARKS, COLLECTION_TRANSIT]
        )
