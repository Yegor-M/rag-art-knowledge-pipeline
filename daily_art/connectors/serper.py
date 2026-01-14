from __future__ import annotations
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from daily_art.connectors.http_client import SESSION
from daily_art.domain.documents import Document

log = logging.getLogger("daily_art.serper")


def _stable_id(prefix: str, text: str) -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{h}"


class SerperClient:
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()

    def search_raw(self, query: str) -> Dict[str, Any]:
        if not self.api_key:
            return {}
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = {"q": query, "gl": "us", "hl": "en"}
        r = SESSION.post(url, headers=headers, data=json.dumps(payload), timeout=20)
        r.raise_for_status()
        return r.json()

    def search_documents(self, query: str, limit: int = 5) -> List[Document]:
        """
        Converts Serper organic results into Document objects.
        We store title/link/snippet as text for now.
        (Later you can add real page fetching.)
        """
        j = self.search_raw(query)
        organic = j.get("organic", []) or []
        docs: List[Document] = []

        for item in organic[: max(1, limit)]:
            if not isinstance(item, dict):
                continue
            title = (item.get("title") or "").strip()
            link = (item.get("link") or "").strip() or None
            snippet = (item.get("snippet") or "").strip()

            # Minimal text: title + snippet (later: fetch full page)
            text = "\n".join([t for t in [title, snippet] if t]).strip()
            if not text:
                continue

            doc_id = _stable_id("serper", (link or "") + "|" + title + "|" + snippet)
            docs.append(
                Document(
                    id=doc_id,
                    title=title,
                    text=text,
                    url=link,
                    source_type="serper",
                    metadata={
                        "query": query,
                        "position": item.get("position"),
                    },
                )
            )

        return docs

    def search_images(self, query: str, num: int = 3) -> List[str]:
        if not self.api_key:
            return []
        url = "https://google.serper.dev/images"
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = {"q": query, "gl": "us", "hl": "en", "num": num}
        r = SESSION.post(url, headers=headers, data=json.dumps(payload), timeout=20)
        r.raise_for_status()
        j = r.json()
        urls: List[str] = []
        for it in j.get("images", []) or []:
            if isinstance(it, dict) and it.get("imageUrl"):
                urls.append(it["imageUrl"])
        # dedupe while preserving order
        seen = set()
        out = []
        for u in urls:
            if u and u not in seen:
                out.append(u)
                seen.add(u)
        return out
