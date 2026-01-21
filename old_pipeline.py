# daily_art/pipeline.py
from __future__ import annotations

from pathlib import Path
from typing import Optional
import json
from config import (
    logger,
    slugify,
    DRAFTS_DIR,
    MESSAGES_DIR,
    save_json,
    load_json,
)
from models import ArtPost, MessagePayload
from sources import SerperClient, WikipediaClient, parse_serper_assets, pick_sources
from daily_art.llm_generators import PostGenerator, RefinementGenerator
from telegram_io import (
    build_caption,
    build_entities_from_markup,
    clamp_entities,
    send_telegram_photo,
    build_caption_with_quote
)

class DailyArtAgent:
    """
    Orchestrates:
      - Serper lookup
      - Wikipedia summary
      - LLM generation
      - deterministic images + citations
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        serper_key: Optional[str] = None,
        enable_wiki: bool = True,
    ):
        self.serper = SerperClient(serper_key)
        self.wiki = WikipediaClient() if enable_wiki else None
        self.generator = PostGenerator(model=model, temperature=0.67)

    def fetch_painting(self, painting: str, author: str, year: str) -> ArtPost:
        query = " ".join([painting, author, year]).strip()

        serper_json = self.serper.search_raw(query)
        _, top_meta = parse_serper_assets(serper_json)

        wiki_q = f"{painting} {author}".strip()
        wiki_summary = self.wiki.summary(wiki_q) if self.wiki else ""

        text_data = self.generator.generate(serper_json, wiki_summary)
        painting_urls = self.serper.search_images(query, num=2)
        sources = pick_sources(top_meta, wiki_summary)

        museum_name = text_data.get("museum", "")
        if museum_name == "" and sources and sources[0].label.lower().startswith("museum"):
            museum_name = sources[0].label.replace("Museum — ", "")

        assembled = {
            **text_data,
            "painting_urls": painting_urls,
            "citations": sources,
            "museum": museum_name,
        }

        return ArtPost(**assembled)


class ArtPipeline:
    """
    High-level tools:
      - draft()
      - refine()
      - build_message()
      - send()
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.agent = DailyArtAgent(model=model)
        self.refiner = RefinementGenerator(model=model)

    # 1) draft

    def draft(self, title: str, author: str, year: str) -> Path:
        slug = f"{slugify(title)}_{year}"
        out_path = DRAFTS_DIR / f"{slug}.json"

        post = self.agent.fetch_painting(title, author, year)
        save_json(out_path, post.model_dump())
        logger.info("Draft saved: %s", f"{slug}.json")
        return out_path

    # 2) refine

    def refine(self, draft_path: str | Path, comments: str) -> Path:
        draft_file = Path(draft_path)
        if not draft_file.exists():
            raise RuntimeError(f"Draft not found: {draft_file}")

        original = load_json(draft_file)
        refined = self.refiner.refine(original, comments)

        slug_base = draft_file.stem
        out_path = DRAFTS_DIR / f"{slug_base}_refined.json"
        save_json(out_path, refined)
        logger.info("Refined draft saved: %s", out_path)
        return out_path

    # 3) build message payload

    def build_message(self, art_path: str | Path) -> Path:
        art_file = Path(art_path)
        if not art_file.exists():
            raise RuntimeError(f"Art JSON not found: {art_file}")

        art_data = load_json(art_file)
        post = ArtPost(**art_data)

        if not post.painting_urls:
            raise RuntimeError("No painting_urls in JSON; cannot build message.")
        photo_url = post.painting_urls[0]

        caption, ents = build_caption_with_quote(post)

        msg = MessagePayload(
            photo_url=photo_url,
            caption=caption,
            caption_entities=ents,
        )

        stem = art_file.stem.replace("_draft", "").replace("_refined", "")
        out_path = MESSAGES_DIR / f"{stem}_post_message.json"
        save_json(out_path, msg.model_dump())
        logger.info("Message payload saved")
        logger.info("---------------------")
        logger.info("\n\n" + caption)
        return out_path

    # 4) send

    def send(self, message_path: str | Path) -> dict:
        msg_file = Path(message_path)
        if not msg_file.exists():
            raise RuntimeError(f"Message JSON not found: {msg_file}")

        data = load_json(msg_file)
        payload = MessagePayload(**data)

        resp = send_telegram_photo(
            photo_url=payload.photo_url,
            caption=payload.caption,
            caption_entities=payload.caption_entities,
        )
        logger.info(
            "Message sent, Telegram message_id: %s",
            resp.get("result", {}).get("message_id"),
        )
        return resp
