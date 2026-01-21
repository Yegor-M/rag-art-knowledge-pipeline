from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from daily_art.core.config import load_settings
from daily_art.core.logging import configure_logging
from daily_art.core.validate import validate_settings
from daily_art.rag.kb import KnowledgeBase


@dataclass
class Metrics:
    n: int
    recall_at_k: float
    mrr: float


def _normalize_url(u: str) -> str:
    return (u or "").strip().rstrip("/")


def _first_relevant_rank(retrieved_urls: List[str], expected_urls: List[str]) -> Optional[int]:
    expected = {_normalize_url(u) for u in expected_urls if u}
    for i, u in enumerate(retrieved_urls, start=1):
        if _normalize_url(u) in expected:
            return i
    return None


def evaluate(gold: List[Dict[str, Any]], top_k: int) -> Metrics:
    s = load_settings()
    configure_logging(s.log_level)
    validate_settings(s, require_telegram=False, require_serper=False)

    kb = KnowledgeBase(openai_api_key=s.openai_api_key)

    hits = 0
    rr_sum = 0.0

    for item in gold:
        q = item["query"]
        expected_urls = item.get("expected_urls", [])
        evidence = kb.search(q, top_k=top_k)

        retrieved_urls = []
        for e in evidence:
            if e.source_url:
                retrieved_urls.append(e.source_url)

        rank = _first_relevant_rank(retrieved_urls, expected_urls)

        print("\n---")
        print("ID:", item.get("id"))
        print("Q:", q)
        print("Expected:", expected_urls)
        print("Retrieved URLs:")
        for i, u in enumerate(retrieved_urls, 1):
            print(f"  {i}. {u}")
        print("First relevant rank:", rank)
        if rank is not None:
            hits += 1
            rr_sum += 1.0 / rank

    n = len(gold) if gold else 1
    return Metrics(
        n=len(gold),
        recall_at_k=hits / n,
        mrr=rr_sum / n,
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Evaluate retrieval quality (Recall@k, MRR).")
    p.add_argument("--gold", type=str, default="daily_art/eval/gold.json")
    p.add_argument("--top-k", type=int, default=6)
    args = p.parse_args()

    gold_path = Path(args.gold)
    gold = json.loads(gold_path.read_text(encoding="utf-8"))

    m = evaluate(gold, top_k=args.top_k)
    print(f"Gold items: {m.n}")
    print(f"Recall@{args.top_k}: {m.recall_at_k:.3f}")
    print(f"MRR@{args.top_k}: {m.mrr:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())