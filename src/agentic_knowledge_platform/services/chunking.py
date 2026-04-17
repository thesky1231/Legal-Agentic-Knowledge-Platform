from __future__ import annotations

from agentic_knowledge_platform.text import estimate_tokens, slugify
from agentic_knowledge_platform.types import ChunkRecord, ParsedDocument


class StructureAwareChunker:
    def __init__(self, max_chars: int = 450, overlap: int = 80) -> None:
        self.max_chars = max_chars
        self.overlap = overlap

    def chunk(self, document: ParsedDocument) -> list[ChunkRecord]:
        chunks: list[ChunkRecord] = []
        buffer = ""
        current_section = document.title
        chunk_index = 1

        def flush() -> None:
            nonlocal buffer, chunk_index
            if not buffer.strip():
                return
            chunk_id = f"{document.document_id}-{slugify(current_section)}-{chunk_index:03d}"
            chunks.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    title=document.title,
                    section=current_section,
                    content=buffer.strip(),
                    source=document.source,
                    metadata=document.metadata.copy(),
                    token_count=estimate_tokens(buffer),
                )
            )
            chunk_index += 1
            buffer = ""

        for element in document.elements:
            if element.kind == "heading":
                if buffer and element.section != current_section:
                    flush()
                current_section = element.section
                continue
            piece = self._format_element(element.kind, element.content)
            if element.section != current_section and buffer:
                flush()
                current_section = element.section
            current_section = element.section
            if not buffer:
                buffer = piece
                continue
            candidate = f"{buffer}\n{piece}".strip()
            if len(candidate) <= self.max_chars:
                buffer = candidate
                continue
            previous_tail = buffer[-self.overlap :] if self.overlap and len(buffer) > self.overlap else ""
            flush()
            buffer = f"{previous_tail}\n{piece}".strip() if previous_tail else piece

        flush()
        return chunks

    def _format_element(self, kind: str, content: str) -> str:
        label = {
            "heading": "标题",
            "paragraph": "段落",
            "list": "列表",
            "table": "表格",
            "formula": "公式",
            "ocr_paragraph": "OCR",
            "transcript": "转写",
        }.get(kind, kind)
        return f"[{label}] {content.strip()}"
