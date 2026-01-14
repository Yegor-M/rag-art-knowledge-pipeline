# daily_art/sources.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

from http_client import SESSION
from models import SourceLink
from config import logger, SERPER_API_KEY


MUSEUM_HOST_HINTS = (
    "mnw.art.pl", "metmuseum.org", "louvre.fr", "nga.gov", "tate.org.uk",
    "rijksmuseum.nl", "artic.edu", "vam.ac.uk", "moma.org", "whitney.org",
    "uffizi.it", "prado.es", "hermitagemuseum.org", "getty.edu",
)


def _dedupe(seq: List[str]) -> List[str]:
    out: List[str] = []
    seen: set = set()
    for x in seq:
        if x and x not in seen:
            out.append(x)
            seen.add(x)
    return out


class SerperClient:
    def __init__(self, api_key: str | None = SERPER_API_KEY):
        self.api_key = api_key or ""

    def search_raw(self, query: str) -> Dict[str, Any]:
        if not self.api_key:
            return {}
        try:
            url = "https://google.serper.dev/search"
            headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
            payload = {"q": query, "gl": "us", "hl": "en"}
            r = SESSION.post(url, headers=headers, data=json.dumps(payload), timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning("Serper search error: %s", e)
            return {}

    def search_images(self, query: str, num: int = 3) -> List[str]:
        if not self.api_key:
            return []
        try:
            url = "https://google.serper.dev/images"
            headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
            payload = {"q": query, "gl": "us", "hl": "en", "num": num}
            r = SESSION.post(url, headers=headers, data=json.dumps(payload), timeout=20)
            r.raise_for_status()
            j = r.json()
            urls: List[str] = []
            for it in j.get("images", []):
                if isinstance(it, dict) and it.get("imageUrl"):
                    urls.append(it["imageUrl"])
            return _dedupe(urls)
        except Exception as e:
            logger.warning("Serper images error: %s", e)
            return []


class WikipediaClient:
    def __init__(self):
        self._runner = WikipediaQueryRun(
            api_wrapper=WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=1500)
        )

    def summary(self, query: str) -> str:
        try:
            return self._runner.run(query)
        except Exception as e:
            logger.warning("Wikipedia error: %s", e)
            return ""


def parse_serper_assets(serper_json: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Returns (organic_raw, top_meta) where top_meta is [{title, link}] for first 5 results.
    """
    organic = serper_json.get("organic", []) or []
    top_meta: List[Dict[str, str]] = []
    for it in organic[:5]:
        if not isinstance(it, dict):
            continue
        top_meta.append(
            {
                "title": it.get("title", ""),
                "link": it.get("link", ""),
            }
        )
    return organic, top_meta


def pick_sources(top_results: List[Dict[str, str]], wiki_summary: str) -> List[SourceLink]:
    sources: List[SourceLink] = []
    n = 1

    def add(label: str, url: str):
        nonlocal n
        if not url:
            return
        sources.append(SourceLink(n=n, label=label or "Source", url=url))
        n += 1

    museum_pick = None
    wiki_pick = None
    fallback_pick = None

    for item in top_results:
        link = item.get("link", "")
        title = item.get("title", "")
        if not museum_pick and any(host in link for host in MUSEUM_HOST_HINTS):
            museum_pick = {"label": f"Museum — {title}".strip() or "Museum page", "url": link}
        if not wiki_pick and "wikipedia.org" in link:
            wiki_pick = {"label": f"Wikipedia — {title}".strip() or "Wikipedia", "url": link}
        if not fallback_pick:
            fallback_pick = {"label": title or "Source", "url": link}

    if museum_pick:
        add(museum_pick["label"], museum_pick["url"])
    if wiki_summary and wiki_pick:
        add(wiki_pick["label"], wiki_pick["url"])
    if not sources and fallback_pick:
        add(fallback_pick["label"], fallback_pick["url"])

    return sources[:2]
