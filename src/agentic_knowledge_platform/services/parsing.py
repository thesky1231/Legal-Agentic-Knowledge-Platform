from __future__ import annotations

import hashlib
import re

from agentic_knowledge_platform.text import normalize_text, top_keywords
from agentic_knowledge_platform.types import DocumentIngestRequest, ParsedDocument, ParsedElement


class MultiModalDocumentParser:
    heading_pattern = re.compile(r"^(#{1,6})\s+(.*)$")
    transcript_pattern = re.compile(r"^\[(\d{2}:\d{2}(?::\d{2})?)\]\s*(.*)$")
    legal_article_pattern = re.compile(
        r"(第\s*[零一二三四五六七八九十百千万0-9]+(?:\s*之\s*[一二三四五六七八九十百千万0-9]+)?\s*条)"
    )
    legal_title_pattern = re.compile(r"^\s*[【\[]([^】\]]+)[】\]]")

    def parse(self, request: DocumentIngestRequest) -> ParsedDocument:
        if request.modality in {"markdown", "text"}:
            return self._parse_markdown_like(request)
        if request.modality == "legal_text":
            return self._parse_legal_text(request)
        if request.modality == "ocr":
            return self._parse_ocr(request)
        if request.modality == "audio":
            return self._parse_transcript(request)
        raise ValueError(f"unsupported modality: {request.modality}")

    def _parse_markdown_like(self, request: DocumentIngestRequest) -> ParsedDocument:
        lines = request.content.splitlines()
        elements: list[ParsedElement] = []
        outline: list[str] = []
        paragraph_buffer: list[str] = []
        current_section = request.title
        line_number = 0

        def flush_paragraph() -> None:
            if not paragraph_buffer:
                return
            elements.append(
                ParsedElement(
                    kind="paragraph",
                    content=normalize_text(" ".join(paragraph_buffer)),
                    section=current_section,
                    metadata={"line": line_number},
                )
            )
            paragraph_buffer.clear()

        index = 0
        while index < len(lines):
            raw_line = lines[index].rstrip()
            stripped = raw_line.strip()
            line_number = index + 1

            if not stripped:
                flush_paragraph()
                index += 1
                continue

            heading_match = self.heading_pattern.match(stripped)
            if heading_match:
                flush_paragraph()
                current_section = heading_match.group(2).strip()
                outline.append(current_section)
                elements.append(
                    ParsedElement(
                        kind="heading",
                        content=current_section,
                        section=current_section,
                        metadata={"level": len(heading_match.group(1)), "line": line_number},
                    )
                )
                index += 1
                continue

            if stripped.startswith("$$"):
                flush_paragraph()
                formula_lines = [stripped]
                index += 1
                while index < len(lines) and not lines[index].strip().startswith("$$"):
                    formula_lines.append(lines[index].rstrip())
                    index += 1
                if index < len(lines):
                    formula_lines.append(lines[index].strip())
                    index += 1
                elements.append(
                    ParsedElement(
                        kind="formula",
                        content="\n".join(line for line in formula_lines if line),
                        section=current_section,
                        metadata={"line": line_number},
                    )
                )
                continue

            if self._looks_like_table_start(lines, index):
                flush_paragraph()
                table_lines = [lines[index].rstrip(), lines[index + 1].rstrip()]
                index += 2
                while index < len(lines) and "|" in lines[index]:
                    table_lines.append(lines[index].rstrip())
                    index += 1
                elements.append(
                    ParsedElement(
                        kind="table",
                        content="\n".join(table_lines),
                        section=current_section,
                        metadata={"rows": max(0, len(table_lines) - 2), "line": line_number},
                    )
                )
                continue

            if stripped.startswith(("- ", "* ", "+ ")) or re.match(r"^\d+\.\s", stripped):
                flush_paragraph()
                list_items = [stripped]
                index += 1
                while index < len(lines):
                    candidate = lines[index].strip()
                    if candidate.startswith(("- ", "* ", "+ ")) or re.match(r"^\d+\.\s", candidate):
                        list_items.append(candidate)
                        index += 1
                        continue
                    break
                elements.append(
                    ParsedElement(
                        kind="list",
                        content="\n".join(list_items),
                        section=current_section,
                        metadata={"count": len(list_items), "line": line_number},
                    )
                )
                continue

            paragraph_buffer.append(stripped)
            index += 1

        flush_paragraph()
        return ParsedDocument(
            document_id=self._make_document_id(request),
            title=request.title,
            source=request.source,
            modality=request.modality,
            language=request.language,
            outline=outline or [request.title],
            elements=elements,
            keywords=top_keywords(request.content),
            metadata=request.metadata.copy(),
        )

    def _parse_ocr(self, request: DocumentIngestRequest) -> ParsedDocument:
        pages = request.content.split("\f")
        elements: list[ParsedElement] = []
        outline: list[str] = []
        for page_index, page in enumerate(pages, start=1):
            section = f"第{page_index}页"
            outline.append(section)
            for paragraph in [normalize_text(block) for block in page.split("\n\n") if normalize_text(block)]:
                elements.append(
                    ParsedElement(
                        kind="ocr_paragraph",
                        content=paragraph,
                        section=section,
                        page=page_index,
                        metadata={"source": "ocr"},
                    )
                )
        return ParsedDocument(
            document_id=self._make_document_id(request),
            title=request.title,
            source=request.source,
            modality=request.modality,
            language=request.language,
            outline=outline or [request.title],
            elements=elements,
            keywords=top_keywords(request.content),
            metadata=request.metadata.copy(),
        )

    def _parse_transcript(self, request: DocumentIngestRequest) -> ParsedDocument:
        elements: list[ParsedElement] = []
        outline = ["会议转写"]
        for index, line in enumerate(request.content.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            match = self.transcript_pattern.match(stripped)
            if match:
                timestamp, content = match.groups()
                elements.append(
                    ParsedElement(
                        kind="transcript",
                        content=normalize_text(content),
                        section="会议转写",
                        metadata={"timestamp": timestamp, "line": index},
                    )
                )
            else:
                elements.append(
                    ParsedElement(
                        kind="transcript",
                        content=normalize_text(stripped),
                        section="会议转写",
                        metadata={"line": index},
                    )
                )
        return ParsedDocument(
            document_id=self._make_document_id(request),
            title=request.title,
            source=request.source,
            modality=request.modality,
            language=request.language,
            outline=outline,
            elements=elements,
            keywords=top_keywords(request.content),
            metadata=request.metadata.copy(),
        )

    def _parse_legal_text(self, request: DocumentIngestRequest) -> ParsedDocument:
        cleaned = self._clean_legal_text(request.content)
        segments = self.legal_article_pattern.split(cleaned)
        elements: list[ParsedElement] = []
        outline: list[str] = []

        for index in range(1, len(segments), 2):
            if index + 1 >= len(segments):
                continue

            article_header = normalize_text(segments[index])
            article_body = normalize_text(segments[index + 1])
            if not article_body:
                continue

            section = article_header
            title_match = self.legal_title_pattern.match(article_body)
            if title_match:
                section = normalize_text(f"{article_header} {title_match.group(1)}")

            outline.append(section)
            elements.append(
                ParsedElement(
                    kind="heading",
                    content=section,
                    section=section,
                    metadata={"level": 2, "article": article_header},
                )
            )
            elements.append(
                ParsedElement(
                    kind="paragraph",
                    content=normalize_text(f"{article_header} {article_body}"),
                    section=section,
                    metadata={"article": article_header},
                )
            )

        if not elements:
            fallback_request = DocumentIngestRequest(
                title=request.title,
                content=cleaned,
                source=request.source,
                modality="text",
                language=request.language,
                tenant_id=request.tenant_id,
                metadata=request.metadata.copy(),
            )
            return self._parse_markdown_like(fallback_request)

        return ParsedDocument(
            document_id=self._make_document_id(request),
            title=request.title,
            source=request.source,
            modality=request.modality,
            language=request.language,
            outline=outline or [request.title],
            elements=elements,
            keywords=top_keywords(cleaned),
            metadata=request.metadata.copy(),
        )

    def _looks_like_table_start(self, lines: list[str], index: int) -> bool:
        if index + 1 >= len(lines):
            return False
        first = lines[index]
        second = lines[index + 1]
        return "|" in first and bool(re.match(r"^\s*\|?[\s:-]+\|[\s|:-]*$", second.strip()))

    def _clean_legal_text(self, text: str) -> str:
        cleaned = text.replace("|", " ")
        noise_patterns = (
            r"---\s*PAGE\s*\d+\s*---",
            r"\b\d+\s*/\s*\d+\b",
            r"JINGSH LAW FIRM",
            r"北京京师律师事务所",
            r"京师律师事务所",
            r"赵荻律师团队",
            r"中国刑事辩护网提供",
            r"电话[:：]\s*0\d{2,3}-[\d-]+",
        )
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
        return cleaned.strip()

    def _make_document_id(self, request: DocumentIngestRequest) -> str:
        seed = f"{request.title}|{request.source}|{request.content[:120]}"
        digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
        safe_title = re.sub(r"[^a-z0-9]+", "-", request.title.lower()).strip("-") or "document"
        return f"doc-{safe_title}-{digest}"
