from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Document(BaseModel):
    id: str
    title: str = ""
    text: str = ""
    url: Optional[str] = None
    source_type: str = "unknown"  # serper | wikipedia | manual
    created_at: str = Field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    id: str
    doc_id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    chunk_id: str
    text: str
    source_title: str = ""
    source_url: Optional[str] = None
    score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    chunk_id: str
    score: float
    payload: Dict[str, Any] = Field(default_factory=dict)
