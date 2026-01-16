from __future__ import annotations

import argparse
import logging
from pathlib import Path

from daily_art.core.config import load_settings
from daily_art.core.fs import ensure_dirs, save_json
from daily_art.core.logging import configure_logging
from daily_art.core.validate import validate_settings
from daily_art.connectors.serper import SerperClient
from daily_art.connectors.wikipedia import WikipediaClient
from daily_art.core.fs import load_json
from daily_art.domain.documents import Document
from daily_art.rag.kb import KnowledgeBase
from daily_art.core.validate import validate_settings

log = logging.getLogger("daily_art.cli")

def cmd_fetch_docs(args: argparse.Namespace) -> int:
    s = load_settings()
    configure_logging(s.log_level)

    # Only require Serper for this command if user requests it
    validate_settings(s, require_telegram=False, require_serper=args.use_serper)

    ensure_dirs(s.data_dir, s.kb_dir, s.drafts_dir, s.messages_dir)

    docs = []

    if args.use_serper:
        serper = SerperClient(api_key=s.serper_api_key)
        docs.extend(serper.search_documents(args.query, limit=args.serper_limit))

    if args.use_wiki:
        wiki = WikipediaClient()
        doc = wiki.get_document(args.query)
        if doc:
            docs.append(doc)

    out_path = Path(args.out) if args.out else (s.kb_dir / "docs.json")
    save_json(out_path, [d.model_dump() for d in docs])
    log.info("Saved %d documents to %s", len(docs), out_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="daily_art", description="RAG knowledge pipeline (Phase 0/1)")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch-docs", help="Fetch documents from Serper/Wikipedia and save as JSON")
    f.add_argument("query", type=str)
    f.add_argument("--out", type=str, default="")
    f.add_argument("--use-serper", action="store_true", help="Enable Serper search")
    f.add_argument("--serper-limit", type=int, default=5)
    f.add_argument("--use-wiki", action="store_true", help="Enable Wikipedia document")
    f.set_defaults(func=cmd_fetch_docs)

    ix = sub.add_parser("kb-index", help="Index documents JSON into vector store")
    ix.add_argument("--docs", required=True, help="Path to docs JSON produced by fetch-docs")
    ix.set_defaults(func=cmd_kb_index)

    qs = sub.add_parser("kb-search", help="Search the KB and print evidence snippets")
    qs.add_argument("query", type=str)
    qs.add_argument("--top-k", type=int, default=6)
    qs.set_defaults(func=cmd_kb_search)

    return p


def cmd_kb_index(args: argparse.Namespace) -> int:
    s = load_settings()
    configure_logging(s.log_level)
    validate_settings(s, require_telegram=False, require_serper=False)

    docs_path = Path(args.docs)
    raw = load_json(docs_path)
    docs = [Document(**d) for d in raw]

    kb = KnowledgeBase(openai_api_key=s.openai_api_key)
    n_chunks = kb.upsert_documents(docs)
    log.info("Indexed %d docs into %d chunks", len(docs), n_chunks)
    return 0


def cmd_kb_search(args: argparse.Namespace) -> int:
    s = load_settings()
    configure_logging(s.log_level)
    validate_settings(s, require_telegram=False, require_serper=False)

    kb = KnowledgeBase(openai_api_key=s.openai_api_key)
    ev = kb.search(args.query, top_k=args.top_k)

    for i, e in enumerate(ev, 1):
        print(f"\n[{i}] score={e.score:.4f} title={e.source_title} url={e.source_url}")
        print(e.text)
    return 0

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())