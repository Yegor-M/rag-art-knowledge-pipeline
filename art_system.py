# daily_art_system.py
from __future__ import annotations

import sys

from pipeline import ArtPipeline


def main():
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  python daily_art_system.py draft <title> <author> <year>\n"
            "  python daily_art_system.py refine <draft_path> --comments \"...\"\n"
            "  python daily_art_system.py build-message <art_json_path>\n"
            "  python daily_art_system.py send <message_json_path>"
        )
        raise SystemExit(2)

    cmd = sys.argv[1]
    pipeline = ArtPipeline()

    if cmd == "draft":
        if len(sys.argv) < 5:
            raise SystemExit("Usage: draft <title> <author> <year>")
        _, _, title, author, year = sys.argv[:5]
        path = pipeline.draft(title, author, year)
        print(path)

    elif cmd == "refine":
        if len(sys.argv) < 3:
            raise SystemExit("Usage: refine <draft_path> --comments \"...\"")
        draft_path = sys.argv[2]
        if "--comments" in sys.argv:
            idx = sys.argv.index("--comments")
            comments = " ".join(sys.argv[idx + 1 :])
        else:
            comments = ""
        path = pipeline.refine(draft_path, comments)
        print(path)

    elif cmd == "build":
        if len(sys.argv) < 3:
            raise SystemExit("Usage: build-message <art_json_path>")
        art_path = sys.argv[2]
        path = pipeline.build_message(art_path)
        print(path)

    elif cmd == "send":
        if len(sys.argv) < 3:
            raise SystemExit("Usage: send <message_json_path>")
        msg_path = sys.argv[2]
        pipeline.send(msg_path)

    else:
        raise SystemExit(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
