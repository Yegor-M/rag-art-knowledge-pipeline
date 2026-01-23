from __future__ import annotations

import hashlib
import logging
from typing import Optional

import requests

from daily_art.domain.documents import Document
from daily_art.core.cache import FileCache

log = logging.getLogger("daily_art.wikipedia")


def _stable_id(prefix: str, text: str) -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{h}"


class WikipediaClient:
    """
    Minimal Wikipedia REST summary fetch.
    Uses Wikipedia page summary endpoint.
    """
    def __init__(self, cache: FileCache | None = None):
        self.cache = cache

    def get_document(self, query: str) -> Optional[Document]:
        q = query.strip()
        if not q:
            return None
        
        cache_key = f"wiki_doc::{query}"
        if self.cache:
            cached = self.cache.get_json("wikipedia", cache_key)
            if cached is not None:
                log.info("using cache")
                return Document(**cached)

        # Wikipedia summary endpoint expects a page title; for queries it may fail sometimes.
        # It's still good for Phase 1. Later you can do search -> page title selection.
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(q)}"
        try:
            r = requests.get(url, timeout=15, headers={"User-Agent": "RAGArtPipeline/1.0"})
            if r.status_code != 200:
                return None
            j = r.json()
            title = (j.get("title") or q).strip()
            extract = (j.get("extract") or "").strip()
            page_url = None
            content_urls = j.get("content_urls") or {}
            desktop = content_urls.get("desktop") or {}
            page_url = desktop.get("page")

            if not extract:
                return None

            doc_id = _stable_id("wiki", page_url or title)
            doc = Document(
                id=doc_id,
                title=title,
                text=extract,
                url=page_url,
                source_type="wikipedia",
                metadata={"query": q},
            )
            log.info(self.cache)
            if doc and self.cache:
                self.cache.set_json("wikipedia", cache_key, doc.model_dump())

            return doc
        except Exception as e:
            log.warning("Wikipedia fetch failed: %s", e)
            return None
