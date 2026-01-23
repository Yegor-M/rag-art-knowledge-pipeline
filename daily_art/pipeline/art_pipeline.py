from __future__ import annotations

from pathlib import Path
from typing import Optional
import logging
from daily_art.core.config import load_settings
from daily_art.core.fs import load_json, save_json
from daily_art.core.config import load_settings
from daily_art.core.fs import save_json
from daily_art.core.fs import ensure_dirs
from daily_art.domain.models import ArtPost, MessagePayload
from daily_art.domain.citations import citations_from_evidence
from daily_art.connectors.serper import SerperClient
from daily_art.connectors.wikipedia import WikipediaClient
from daily_art.llm_generators import PostGenerator
from daily_art.rag.kb import KnowledgeBase
from daily_art.core.telegram_io import build_caption
from daily_art.connectors.telegram import TelegramClient, TelegramConfig

log = logging.getLogger("daily_art.pipeline")


class ArtPipeline:
    def __init__(self, model: str | None = None):
        self.s = load_settings()
        ensure_dirs(self.s.data_dir, self.s.drafts_dir, self.s.messages_dir, self.s.kb_dir)

        self.model = model or self.s.openai_model
        self.telegram = TelegramClient(TelegramConfig(bot_token=self.s.telegram_bot_token, chat_id=self.s.telegram_chat_id))
        self.serper = SerperClient(api_key=self.s.serper_api_key)
        self.wiki = WikipediaClient()
        self.kb = KnowledgeBase(openai_api_key=self.s.openai_api_key)
        
        self.generator = PostGenerator(model=self.model)

    def build_draft(self, title: str, author: str, year: str) -> Path:
        query = " ".join([title, author, year]).strip()

        # 1) Fetch docs (deterministic inputs)
        docs = []
        if self.s.serper_api_key:
            docs.extend(self.serper.search_documents(query, limit=5))
        wiki_doc = self.wiki.get_document(f"{title} {author}".strip())
        if wiki_doc:
            docs.append(wiki_doc)

        # 2) Upsert into KB + retrieve evidence
        if docs:
            self.kb.upsert_documents(docs)

        evidence = self.kb.search(query, top_k=6)

        # 3) Generate narrative from evidence
        meta = {"title": title, "author": author, "year": year}
        text_data = self.generator.generate(meta=meta, evidence=evidence)

        # 4) Deterministic painting image urls
        painting_urls = self.serper.search_images(query, num=2) if self.s.serper_api_key else []

        # 5) Deterministic citations from evidence
        citations = citations_from_evidence(evidence, max_sources=2)

        post = ArtPost(**{
            **text_data,
            "painting_urls": painting_urls,
            "citations": citations,
        })

        slug = f"{title.lower().replace(' ', '_')}_{year}"
        out_path = self.s.drafts_dir / f"{slug}.json"
        save_json(out_path, post.model_dump())
        log.info("Draft saved: %s", out_path)
        return out_path
    
    def build_message(self, art_json_path: Path) -> Path:
        data = load_json(art_json_path)
        post = ArtPost(**data)

        if not post.painting_urls:
            raise RuntimeError("No painting_urls in ArtPost; enable Serper images or set one manually.")
        photo_url = post.painting_urls[0]

        caption, entities = build_caption(post)

        msg = MessagePayload(photo_url=photo_url, caption=caption, caption_entities=entities)

        out_path = self.s.messages_dir / f"{art_json_path.stem}_message.json"
        save_json(out_path, msg.model_dump())
        return out_path


    def send(self, message_json_path: Path) -> dict:
        data = load_json(message_json_path)
        payload = MessagePayload(**data)
        return self.telegram.send_photo(
            photo_url=payload.photo_url,
            caption=payload.caption,
            caption_entities=payload.caption_entities,
        )

