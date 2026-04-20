from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.services.local_corpus import detect_modality, read_content


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Post a local file into the running backend knowledge base.")
    parser.add_argument("file", help="Path to the local document file.")
    parser.add_argument("--title", help="Document title. Defaults to the file stem.")
    parser.add_argument("--tenant-id", default="demo", help="Tenant id for retrieval isolation.")
    parser.add_argument("--source", help="Logical source label returned in citations.")
    parser.add_argument(
        "--modality",
        choices=["markdown", "text", "legal_text", "ocr", "audio"],
        help="Override modality. Defaults to markdown for .md and legal_text for .txt.",
    )
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000",
        help="Running backend base URL.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    path = Path(args.file).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"document file not found: {path}")

    payload = {
        "title": args.title or path.stem,
        "content": read_content(path),
        "source": args.source or str(path),
        "modality": detect_modality(path, args.modality),
        "tenant_id": args.tenant_id,
    }

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{args.api_base.rstrip('/')}/documents/ingest",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            print(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(detail, file=sys.stderr)
        raise SystemExit(exc.code) from exc


if __name__ == "__main__":
    main()
