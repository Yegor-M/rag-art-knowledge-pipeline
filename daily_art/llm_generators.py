from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from daily_art.core.config import load_settings
from daily_art.domain.documents import Evidence


class PostGenerator:
    """
    Evidence-grounded generator.
    The model sees ONLY: meta + evidence snippets.
    """
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.5):
        s = load_settings()
        # ensure OpenAI key is picked up from env; LangChain reads env var by default,
        # but this keeps it explicit in your settings flow.
        self.llm = ChatOpenAI(model=model, temperature=temperature, api_key=s.openai_api_key)

        self.template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You write structured, evidence-grounded art notes.\n"
                    "You MUST use ONLY the provided EVIDENCE SNIPPETS for factual claims.\n"
                    "Return ONLY a single JSON object with exactly these keys:\n"
                    "title, year, art_style, artist, artist_info, related_quote, quote_author, "
                    "painting_features, intro, context, meaning, conclusion, museum, unique_fact.\n"
                    "No extra keys. No markdown. No citations. No URLs.",
                ),
                (
                    "human",
                    "META:\n{meta_json}\n\n"
                    "EVIDENCE SNIPPETS (ranked):\n{evidence_text}\n\n"
                    "OUTPUT: JSON object only.",
                ),
            ]
        )

    def generate(self, meta: Dict[str, Any], evidence: List[Evidence]) -> Dict[str, Any]:
        lines = []
        for i, e in enumerate(sorted(evidence, key=lambda x: x.score, reverse=True)[:6], 1):
            src = (e.source_title or "").strip()
            url = (e.source_url or "").strip()
            head = f"[{i}] {src} ({url})" if url else f"[{i}] {src}"
            snippet = (e.text or "").strip()
            lines.append(head)
            lines.append(snippet)
            lines.append("")

        args = {
            "meta_json": json.dumps(meta, ensure_ascii=False),
            "evidence_text": "\n".join(lines).strip(),
        }

        raw = (self.template | self.llm).invoke(args).content

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\{[\s\S]*\}", raw)
            if not m:
                raise
            return json.loads(m.group())
