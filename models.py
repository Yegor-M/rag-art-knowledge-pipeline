# daily_art/models.py
from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field


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


class MessagePayload(BaseModel):
    photo_url: str
    caption: str
    caption_entities: List[Dict[str, Any]]
