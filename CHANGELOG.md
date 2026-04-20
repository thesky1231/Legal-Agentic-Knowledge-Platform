# Changelog

All notable changes to this repository will be documented in this file.

The format is intentionally lightweight and focused on public release milestones.

## [0.1.0] - 2026-04-17

### Added

- Legal-domain agentic knowledge platform positioning built on a Python backend architecture.
- Structure-aware document ingestion pipeline for markdown, OCR text, and transcript-style inputs.
- Grounded RAG workflow with chunking, embeddings, vector retrieval, reranking, and citation-based answering.
- Legal query policy with question typing, conservative refusal behavior, and confidence-aware answer shaping.
- Single-agent and team-agent flows with reviewer-backed delivery.
- Model routing layer with retry, rate limiting, circuit breaker, and fallback behavior.
- Run audit storage, observability endpoints, metrics output, and evaluation entry points.
- OpenAI-compatible model adapters, Qdrant adapter, Docker assets, and GitHub Actions CI.
- Imported offline legal benchmark assets from the earlier legal RAG project for benchmark-style evaluation snapshots.

### Notes

- The legal benchmark figures in this repository are offline evaluation snapshots, not online production metrics.
- This release is the first public version intended to demonstrate backend, RAG, and agent system design.
