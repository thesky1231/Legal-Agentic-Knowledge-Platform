# Resume Bullets

## Version A

- Designed and implemented an agentic knowledge platform in Python/FastAPI covering document parsing, RAG retrieval, grounded citation answering, model routing, and voice narration orchestration.
- Built a modular retrieval pipeline with structure-aware chunking, pluggable embeddings, vector backends, reranking, and hallucination control through confidence thresholds and citation enforcement.
- Implemented a multi-model orchestration layer with rate limiting, retries, circuit breaking, and fallback routing, enabling migration from offline demo mode to OpenAI-compatible production APIs.
- Delivered both a ReAct-style single-agent workflow and a multi-agent collaboration flow with reviewer and narration roles, plus auditable run history for debugging and demos.
- Added tenant-aware retrieval isolation, SQLite-backed run persistence, offline evaluation datasets, API key protection, structured request logging, and Prometheus-style metrics to move the project closer to production expectations.
- Merged a legal-domain RAG case study into the platform by carrying over question classification, refusal control, and historical retrieval/answer evaluation datasets with 100% answer and citation correctness on the imported legal benchmark snapshot.

## Version B

- Developed a portfolio-ready enterprise knowledge QA backend that unifies long-document parsing, RAG, API orchestration, and agent execution.
- Abstracted model, embedding, vector store, and voice providers so the same codebase can run in offline demo mode or switch to OpenAI-compatible endpoints and Qdrant.
- Added engineering controls including rate limits, circuit breakers, retries, and strict citation output to reduce hallucinations and improve service reliability.

## Interview keywords

- FastAPI
- RAG
- citation grounding
- model routing
- fallback
- circuit breaker
- rate limiting
- Qdrant
- OpenAI-compatible API
- ReAct agent
- observability
- Prometheus metrics
- structured logging
- TTS / A2F integration
