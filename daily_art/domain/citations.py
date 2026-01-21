from __future__ import annotations

from typing import List, Optional
from urllib.parse import urlparse

from daily_art.domain.documents import Evidence
from daily_art.domain.models import SourceLink


def _host(url: Optional[str]) -> str:
    if not url:
        return ""
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def citations_from_evidence(evidence: List[Evidence], max_sources: int = 2) -> List[SourceLink]:
    """
    Deterministic: pick unique source URLs from evidence in ranked order.
    """
    out: List[SourceLink] = []
    seen = set()
    n = 1

    for e in sorted(evidence, key=lambda x: x.score, reverse=True):
        url = (e.source_url or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)

        label = (e.source_title or "").strip() or _host(url) or "Source"
        out.append(SourceLink(n=n, label=label, url=url))
        n += 1

        if len(out) >= max_sources:
            break

    return out