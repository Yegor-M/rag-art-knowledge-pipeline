from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List

from daily_art.domain.documents import Document, Chunk


@dataclass(frozen=True)
class ChunkingConfig:
    max_chars: int = 900
    min_chars: int = 200


def _chunk_id(doc_id: str, idx: int, text: str) -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"{doc_id}_c{idx}_{h}"


class Chunker:
    def __init__(self, cfg: ChunkingConfig | None = None):
        self.cfg = cfg or ChunkingConfig()

    def chunk(self, doc: Document) -> List[Chunk]:
        text = (doc.text or "").strip()
        if not text:
            return []

        # naive paragraph split
        paras = [p.strip() for p in text.split("\n") if p.strip()]
        chunks: List[str] = []
        buf: List[str] = []
        buf_len = 0

        def flush():
            nonlocal buf, buf_len
            if buf:
                chunks.append("\n".join(buf).strip())
            buf = []
            buf_len = 0

        for p in paras:
            if buf_len + len(p) + 1 <= self.cfg.max_chars:
                buf.append(p)
                buf_len += len(p) + 1
            else:
                flush()
                # if single paragraph too large, hard-split
                if len(p) > self.cfg.max_chars:
                    for i in range(0, len(p), self.cfg.max_chars):
                        part = p[i : i + self.cfg.max_chars].strip()
                        if part:
                            chunks.append(part)
                else:
                    buf.append(p)
                    buf_len = len(p)

        flush()

        # filter tiny chunks
        out: List[Chunk] = []
        for i, ch_text in enumerate(chunks):
            if len(ch_text) < self.cfg.min_chars and len(chunks) > 1:
                continue
            out.append(
                Chunk(
                    id=_chunk_id(doc.id, i, ch_text),
                    doc_id=doc.id,
                    text=ch_text,
                    metadata={
                        "source_type": doc.source_type,
                        "title": doc.title,
                        "url": doc.url,
                        "chunk_index": i,
                    },
                )
            )
        return out
