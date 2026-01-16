from __future__ import annotations

from dataclasses import dataclass
from typing import List

from openai import OpenAI


@dataclass(frozen=True)
class EmbeddingConfig:
    model: str = "text-embedding-3-small"


class Embedder:
    def __init__(self, api_key: str, cfg: EmbeddingConfig | None = None):
        self.client = OpenAI(api_key=api_key)
        self.cfg = cfg or EmbeddingConfig()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        resp = self.client.embeddings.create(model=self.cfg.model, input=texts)
        # OpenAI returns in order
        return [d.embedding for d in resp.data]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]