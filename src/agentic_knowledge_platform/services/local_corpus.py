from __future__ import annotations

import os
import re
from pathlib import Path

from agentic_knowledge_platform.types import DocumentIngestRequest, IngestionResult

SUPPORTED_SUFFIXES = {".txt", ".text", ".md", ".markdown", ".pdf"}


def detect_modality(path: Path, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".txt", ".text", ".pdf"}:
        return "legal_text"
    return "text"


def read_content(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return _read_pdf_text(path)
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"unable to decode file: {path}")


def _read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on local runtime env.
        raise RuntimeError(
            "Reading PDF bootstrap corpora requires `pypdf`. Use the py312_cuda environment or install pypdf."
        ) from exc

    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


def collect_document_paths(path_spec: str) -> list[Path]:
    items = [item.strip() for item in re.split(r"[;\n]+", path_spec) if item.strip()]
    paths: list[Path] = []
    seen: set[Path] = set()

    for raw_item in items:
        target = Path(raw_item).expanduser().resolve()
        if not target.exists():
            raise FileNotFoundError(f"bootstrap knowledge path not found: {target}")
        if target.is_file():
            if target.suffix.lower() in SUPPORTED_SUFFIXES and target not in seen:
                paths.append(target)
                seen.add(target)
            continue
        for candidate in sorted(target.rglob("*")):
            if not candidate.is_file():
                continue
            if candidate.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            paths.append(resolved)
            seen.add(resolved)

    return paths


def bootstrap_local_corpus(
    knowledge_base,
    path_spec: str,
    tenant_id: str = "demo",
) -> list[IngestionResult]:
    results: list[IngestionResult] = []
    for path in collect_document_paths(path_spec):
        request = DocumentIngestRequest(
            title=path.stem,
            content=read_content(path),
            source=str(path),
            modality=detect_modality(path),
            tenant_id=tenant_id,
            metadata={"bootstrap": "local_corpus", "tenant_id": tenant_id},
        )
        results.append(knowledge_base.ingest(request))
    return results
