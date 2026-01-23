from __future__ import annotations
from dataclasses import dataclass
from typing import List
from openai import OpenAI
from daily_art.core.cache import FileCache, sha1_text


@dataclass(frozen=True)
class EmbeddingConfig:
    model: str = "text-embedding-3-small"

class Embedder:
    def __init__(self, api_key: str, cfg: EmbeddingConfig | None = None, cache: FileCache | None = None):
        self.client = OpenAI(api_key=api_key)
        self.cfg = cfg or EmbeddingConfig()
        self.cache = cache

    def _cache_key(self, text: str) -> str:
        # include model so changing model invalidates cache
        return f"{self.cfg.model}::{sha1_text(text)}"

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        # 1) read cache
        vectors: List[Optional[List[float]]] = [None] * len(texts)
        missing_texts: List[str] = []
        missing_idx: List[int] = []

        for i, t in enumerate(texts):
            if self.cache:
                cached = self.cache.get_json("embeddings", self._cache_key(t))
                if isinstance(cached, list) and cached:
                    vectors[i] = cached
                    continue
            missing_texts.append(t)
            missing_idx.append(i)

        # 2) embed only missing
        if missing_texts:
            resp = self.client.embeddings.create(model=self.cfg.model, input=missing_texts)
            new_vecs = [d.embedding for d in resp.data]

            # 3) write cache + fill
            for j, vec in enumerate(new_vecs):
                i = missing_idx[j]
                vectors[i] = vec
                if self.cache:
                    self.cache.set_json("embeddings", self._cache_key(texts[i]), vec)

        return [v for v in vectors if v is not None]

    def embed_query(self, text: str) -> List[float]:
        # queries you typically don't cache, but you *can*
        return self.client.embeddings.create(model=self.cfg.model, input=[text]).data[0].embedding
