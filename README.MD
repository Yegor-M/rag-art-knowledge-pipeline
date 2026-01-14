# Daily Art System 🎨

A small, scriptable pipeline that generates engaging art insights and posts them to a Telegram channel.

The pipeline is designed to be **modular and reviewable**:

1. Fetch & generate an **art draft** (JSON) using web sources + LLM.
2. Optionally **refine** the draft with your comments.
3. Build a **Telegram-ready message JSON** (caption + entities + image URL).
4. **Send** the post to a Telegram chat/channel.

Everything is driven from a simple CLI (`art_system.py`).

---

## Features

- Uses **Serper.dev** + **Wikipedia** for factual context.
- LLM (OpenAI) writes narrative fields in a modern, vivid style.
- Deterministic:
  - URLs & citations come from search, not hallucinated.
  - Text is structured into named fields (`intro`, `context`, `meaning`, `unique_fact`, etc).
- Generates Telegram messages with:
  - Markdown-like formatting (bold, italic, spoilers) mapped to `caption_entities`.
  - Proper UTF-16 offsets (so formatting doesn’t break).
- Supports **human-in-the-loop** workflow:
  - You can review / edit JSON drafts.
  - You can refine them via LLM using your comments.
  - You only send to Telegram when you’re happy.

---

## Project Structure

Typical layout (simplified):

```text
urban_dreams_miniapp/
  daily_art/
    art_system.py          # CLI entrypoint
    config.py              # env, logging, data paths, JSON helpers
    http_client.py         # requests session with retry/backoff
    models.py              # Pydantic models (ArtPost, MessagePayload, SourceLink)
    sources.py             # Serper + Wikipedia clients, source picking
    llm_generators.py      # PostGenerator + RefinementGenerator
    telegram_io.py         # caption builder, markup parser, Telegram sender
    pipeline.py            # ArtPipeline: draft / refine / build_message / send
    data/
      drafts/              # raw & refined art posts (*.json)
      messages/            # ready-to-send Telegram payloads (*.json)

Requirements: Python 3.11+

Dependencies (install via requirements.txt):
pip install -r requirements.txt

License MIT