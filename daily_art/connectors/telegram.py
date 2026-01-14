# daily_art/telegram_io.py
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

from http_client import SESSION
from models import ArtPost
from config import logger, BOT_TOKEN, CHAT_ID


# ---- UTF-16 helpers ----

def utf16_len(s: str) -> int:
    return len(s.encode("utf-16-le")) // 2


def utf16_offset(s: str, idx: int) -> int:
    return len(s[:idx].encode("utf-16-le")) // 2


# ---- Regex for inline styles ----

LINK_RE   = re.compile(r'\[([^\]]+?)\]\((https?://[^\s)]+)\)')
BOLD_RE   = re.compile(r'\*\*(.+?)\*\*')
ITALIC_RE = re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)')
UNDER_RE  = re.compile(r'__(.+?)__')
STRIKE_RE = re.compile(r'~~(.+?)~~')
CODE_RE   = re.compile(r'`([^`\n]+?)`')
SPOILER_RE= re.compile(r'\|\|(.+?)\|\|')


def _strip_and_entity(
    text: str,
    pattern: re.Pattern,
    entity_type: str,
    url_group: Optional[int] = None,
) -> Tuple[str, List[Dict]]:
    entities: List[Dict] = []
    cursor = 0
    out: List[str] = []

    for m in pattern.finditer(text):
        start, end = m.span()
        inner_text = m.group(1) if m.lastindex and m.lastindex >= 1 else None
        url = (
            m.group(url_group)
            if url_group and m.lastindex and m.lastindex >= url_group
            else None
        )

        if inner_text is None:
            continue

        out.append(text[cursor:start])
        before_out = "".join(out)
        start_out_idx = len(before_out)

        out.append(inner_text)

        clean_inner = inner_text.rstrip()
        trimmed = len(inner_text) - len(clean_inner)

        offset = utf16_offset("".join(out), start_out_idx)
        length_units = utf16_len(clean_inner)

        if length_units > 0:
            ent: Dict[str, Any] = {
                "type": entity_type,
                "offset": offset,
                "length": length_units,
            }
            if entity_type == "text_link" and url:
                ent["url"] = url
            entities.append(ent)

        cursor = end
        if trimmed:
            out.append(inner_text[-trimmed:])

    out.append(text[cursor:])
    return "".join(out), entities

from typing import List, Dict, Tuple

def build_caption_with_quote(post: ArtPost, hashtag: str = "#art_insight") -> Tuple[str, List[Dict]]:
    entities: List[Dict] = []

    # --- ЦИТАТА ---
    quote = (getattr(post, "related_quote", "") or "").strip()
    quote_author = (getattr(post, "quote_author", "") or "").strip()

    quote_block = ""
    if quote:
        # текст цитаты без markdown-звёздочек
        if quote_author:
            quote_line = f'"{quote}" — {quote_author}'
        else:
            quote_line = f'"{quote}"'

        quote_block = quote_line + "\n\n"

        # делаем её курсивной через entity
        entities.append(
            {
                "type": "italic",
                "offset": 0,                          # с начала caption
                "length": utf16_len(quote_line),      # только сама цитата/строка, без \n\n
            }
        )

    # --- ОСНОВНОЕ ТЕЛО ПОСТА (БЕЗ ЦИТАТЫ) ---
    lines: List[str] = []

    lines.append(f'**Name:** {post.title}')
    lines.append(f'**Year:** {post.year}')
    art_style = getattr(post, "art_style", "")
    if art_style:
        lines.append(f'**Style:** {art_style}')
    lines.append("")

    if post.painting_features:
        lines.append(post.painting_features)
    if post.context:
        lines.append(post.context)
    if post.meaning:
        lines.append(post.meaning)
    if post.conclusion:
        lines.append(post.conclusion)

    if post.unique_fact:
        lines.append(f"\n||{post.unique_fact}||")

    lines.append("")
    lines.append(hashtag)

    body = "\n".join([ln for ln in lines if ln is not None]).strip()

    # --- ПАРСИМ МАРКДАУН ТОЛЬКО ДЛЯ body ---
    clean_body, body_entities = build_entities_from_markup(body)
    body_entities = clamp_entities(clean_body, body_entities)

    # --- СДВИГАЕМ entity из body НА ДЛИНУ ЦИТАТЫ ---
    shift = utf16_len(quote_block)
    for e in body_entities:
        e["offset"] += shift

    # финальный caption и все entities
    caption = quote_block + clean_body
    entities.extend(body_entities)

    # на всякий случай отсортируем по offset
    entities.sort(key=lambda e: e["offset"])

    return caption, entities



def build_entities_from_markup(text: str) -> Tuple[str, List[Dict]]:
    entities: List[Dict] = []

    text, ents = _strip_and_entity(text, BOLD_RE, "bold")
    entities.extend(ents)

    text, ents = _strip_and_entity(text, LINK_RE, "text_link", url_group=2)
    entities.extend(ents)

    text, ents = _strip_and_entity(text, CODE_RE, "code")
    entities.extend(ents)

    text, ents = _strip_and_entity(text, ITALIC_RE, "italic")
    entities.extend(ents)

    text, ents = _strip_and_entity(text, UNDER_RE, "underline")
    entities.extend(ents)

    text, ents = _strip_and_entity(text, STRIKE_RE, "strikethrough")
    entities.extend(ents)

    text, ents = _strip_and_entity(text, SPOILER_RE, "spoiler")
    entities.extend(ents)

    entities = [e for e in entities if e["length"] > 0]
    entities.sort(key=lambda e: e["offset"])
    return text, entities


def clamp_entities(text: str, entities: List[Dict]) -> List[Dict]:
    max_len = utf16_len(text)
    safe: List[Dict] = []
    for e in entities:
        if e["offset"] < max_len:
            if e["offset"] + e["length"] > max_len:
                e["length"] = max_len - e["offset"]
            if e["length"] > 0:
                safe.append(e)
    return safe


def build_caption(post: ArtPost, hashtag: str = "#art_insight") -> str:
    quote = post.related_quote.strip()
    quote_author = (post.quote_author or "").strip()

    lines: List[str] = []
    if quote:
        if quote_author:
            lines.append(f'*"{quote}"* — {quote_author}')
        else:
            lines.append(f'*"{quote}"*')
        lines.append("")

    lines.append(f'**Name:** {post.title}')
    lines.append(f'**Year:** {post.year}')
    if post.art_style:
        lines.append(f'**Genre:** {post.art_style}')
    lines.append("")

    if post.painting_features:
        lines.append(post.painting_features)
    if post.context:
        lines.append(post.context)
    if post.meaning:
        lines.append(post.meaning)
    # if post.conclusion:
    #     lines.append(post.conclusion)

    if post.unique_fact:
        lines.append(f"\n||{post.unique_fact}||")

    lines.append("")
    lines.append(hashtag)

    caption = "\n".join([ln for ln in lines if ln is not None])
    return caption.strip()


def send_telegram_photo(
    photo_url: str,
    caption: str,
    caption_entities: List[Dict],
    bot_token: str = BOT_TOKEN,
    chat_id: str = CHAT_ID,
) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "caption_entities": json.dumps(caption_entities),
    }
    r = SESSION.post(url, data=payload, timeout=20)
    logger.info("Telegram response: %s", r.text)
    r.raise_for_status()
    return r.json()