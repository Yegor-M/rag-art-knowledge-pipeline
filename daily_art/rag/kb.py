from __future__ import annotations

from dataclasses import dataclass
from typing import List

from daily_art.domain.documents import Document, Evidence
from daily_art.rag.chunking import Chunker, ChunkingConfig
from daily_art.rag.embeddings import Embedder, EmbeddingConfig
from daily_art.rag.vectordb import VectorStore, QdrantConfig


@dataclass(frozen=True)
class KnowledgeBaseConfig:
    chunking: ChunkingConfig = ChunkingConfig()
    embeddings: EmbeddingConfig = EmbeddingConfig()
    qdrant: QdrantConfig = QdrantConfig()
    top_k: int = 6


class KnowledgeBase:
    def __init__(self, *, openai_api_key: str, cfg: KnowledgeBaseConfig | None = None):
        self.cfg = cfg or KnowledgeBaseConfig()
        self.chunker = Chunker(self.cfg.chunking)
        self.embedder = Embedder(api_key=openai_api_key, cfg=self.cfg.embeddings)

        # vector size depends on embedding model; we can infer by embedding one small text
        sample_vec = self.embedder.embed_query("vector-size-probe")
        self.store = VectorStore(cfg=self.cfg.qdrant, vector_size=len(sample_vec))

    def upsert_documents(self, docs: List[Document]) -> int:
        chunks = []
        for d in docs:
            chunks.extend(self.chunker.chunk(d))
        if not chunks:
            return 0

        vectors = self.embedder.embed_texts([c.text for c in chunks])
        self.store.upsert(chunks, vectors)
        return len(chunks)

    def search(self, query: str, top_k: int | None = None) -> List[Evidence]:
        k = top_k or self.cfg.top_k
        qvec = self.embedder.embed_query(query)
        results = self.store.search(qvec, top_k=k)

        evidence: List[Evidence] = []
        for r in results:
            payload = r.payload or {}
            evidence.append(
                Evidence(
                    chunk_id=r.chunk_id,
                    text=(payload.get("text") or "")[:900],
                    source_title=str(payload.get("title") or ""),
                    source_url=payload.get("url"),
                    score=r.score,
                    metadata={k: v for k, v in payload.items() if k not in {"text"}},
                )
            )
        return evidence
