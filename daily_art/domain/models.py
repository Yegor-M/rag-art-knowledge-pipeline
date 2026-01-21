# daily_art/models.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Document(BaseModel):
    id: str
    title: str
    text: str
    url: str | None
    source_type: str # (serper/wiki/manual)
    metadata: dict

class Chunk(BaseModel):
    id: str
    doc_id: str
    text: str
    metadata: dict # (position, title, url)

class Evidence(BaseModel):
    """
    A single grounded piece of information retrieved from your KB / search layer.

    Keep it small and explicit:
    - text: the snippet the LLM is allowed to use
    - source_title/url: where it came from
    - score: retrieval score (optional but useful for debugging)
    """
    chunk_id: str = ""
    text: str = Field(default="", description="Grounded snippet text for the model to use.")
    source_title: str = ""
    source_url: Optional[str] = None
    score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceLink(BaseModel):
    n: int
    label: str = Field(default="Source")
    url: str = Field(default="")


class ArtPost(BaseModel):
    # narrative fields
    title: str = ""
    year: str|int = ""
    art_style: str = ""
    artist: str = ""
    artist_info: str = ""
    related_quote: str = ""    # main quote line
    quote_author: str = ""      # who said it (optional; often same as artist)
    intro: str = ""
    context: str = ""
    meaning: str = ""
    conclusion: str = ""
    museum: str = ""
    unique_fact: str = ""
    painting_features: str = ""

    # non-LLM
    painting_urls: List[str] = Field(default_factory=list)
    citations: List[SourceLink] = Field(default_factory=list)


# class MessagePayload(BaseModel):
#     photo_url: str
#     caption: str
#     caption_entities: List[Dict[str, Any]]
