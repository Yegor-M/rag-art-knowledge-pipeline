from __future__ import annotations

import argparse
import logging
from pathlib import Path

from daily_art.core.config import load_settings
from daily_art.core.fs import ensure_dirs, save_json
from daily_art.core.logging import configure_logging
from daily_art.core.validate import validate_settings

# Phase 1 imports
from daily_art.connectors.serper import SerperClient
from daily_art.connectors.wikipedia import WikipediaClient


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

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())