from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from daily_art.domain.documents import Chunk, SearchResult


@dataclass(frozen=True)
class QdrantConfig:
    host: str = "localhost"
    port: int = 6333
    collection: str = "rag_docs"


def _qdrant_point_id(stable_text_id: str) -> str:
    # Stable UUID derived from chunk_id
    return str(uuid.uuid5(uuid.NAMESPACE_URL, stable_text_id))


class VectorStore:
    def __init__(self, cfg: QdrantConfig, vector_size: int):
        self.cfg = cfg
        self.client = QdrantClient(host=cfg.host, port=cfg.port)
        self._ensure_collection(vector_size)

    def _ensure_collection(self, vector_size: int) -> None:
        existing = {c.name for c in self.client.get_collections().collections}
        if self.cfg.collection in existing:
            return

        self.client.create_collection(
            collection_name=self.cfg.collection,
            vectors_config=qm.VectorParams(
                size=vector_size,
                distance=qm.Distance.COSINE,
            ),
        )

    def upsert(self, chunks: List[Chunk], vectors: List[List[float]]) -> None:
        assert len(chunks) == len(vectors)

        points: List[qm.PointStruct] = []
        for ch, vec in zip(chunks, vectors):
            payload: Dict[str, Any] = {
                "chunk_id": ch.id,
                "doc_id": ch.doc_id,
                "text": ch.text,
                **(ch.metadata or {}),
            }

            points.append(
                qm.PointStruct(
                    id=_qdrant_point_id(ch.id),
                    vector=vec,
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=self.cfg.collection,
            points=points,
            wait=True,
        )

    def search(self, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        """
        Compatible with modern qdrant-client versions.
        """
        if hasattr(self.client, "query_points"):
            res = self.client.query_points(
                collection_name=self.cfg.collection,
                query=query_vector,
                limit=top_k,
                with_payload=True,
            )
            hits = res.points
        else:
            hits = self.client.search(
                collection_name=self.cfg.collection,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
            )

        out: List[SearchResult] = []
        for h in hits:
            payload = h.payload or {}
            out.append(
                SearchResult(
                    chunk_id=str(payload.get("chunk_id") or ""),
                    score=float(h.score or 0.0),
                    payload=payload,
                )
            )
        return out
