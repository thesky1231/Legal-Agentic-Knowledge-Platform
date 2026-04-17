# Interview Guide

## One-minute version

This project is an agentic knowledge platform rather than a simple chatbot shell. It starts with document understanding, converts parsed content into structured chunks, retrieves evidence through RAG, generates grounded answers with citations, and then optionally turns the answer into a speech script for TTS or digital human rendering.

## Five talking points

1. I designed the project around replaceable interfaces, so parser, embeddings, vector store, model client, and voice pipeline can all change without rewriting the workflow layer.
2. The RAG chain is intentionally complete: parse, chunk, embed, retrieve, rerank, grounded answer, and citation formatting.
3. The model orchestration layer is not a raw SDK call. It includes routing by task type, retry policy, rate limiting, circuit breaking, and fallback.
4. The agent is implemented as a ReAct-style execution loop with explicit steps and observations, and I extended it into a team mode with a reviewer agent and a narration agent.
5. I kept the default mode offline for demos, but added adapters for OpenAI-compatible models and Qdrant, plus tenant-aware retrieval, SQLite-backed audit history, API key auth, structured request logging, `/ops/overview`, `/metrics`, and a legal-domain evaluation case study with refusal control so the same project can evolve toward production.

## If the interviewer asks what you would do next

- Add async ingestion jobs and queue-based GPU scheduling.
- Replace the lexical reranker with a cross-encoder or vendor rerank API.
- Extend the existing request metrics and structured logs into distributed tracing for each agent step.
- Add multi-tenant knowledge bases and permission checks.
- Add real OCR and ASR connectors for PDF scans and meeting transcripts.
- Persist agent run history to Redis or a database instead of in-memory storage, then expose dashboards for audit and debugging.
