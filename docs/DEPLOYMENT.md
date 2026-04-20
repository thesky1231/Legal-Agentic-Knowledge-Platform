# Deployment Guide

## Local demo mode

Use the default configuration when you want a fully offline demo:

```bash
python -m unittest discover -s tests -v
python scripts/demo_cli.py
python scripts/demo_showcase.py
```

The runnable demo scripts now ingest:

- `examples/legal/legal_assistant_handbook.md`

This mode uses:

- `MODEL_PROVIDER=stub`
- `EMBEDDING_PROVIDER=hash`
- `VECTOR_STORE_BACKEND=memory`
- `RUN_STORE_BACKEND=memory`

## Containerized API

Build and run the service:

```bash
docker compose up --build
```

This is the fastest reproducible deployment path for outside users.

Once the service starts, open:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/ops/overview`
- `GET http://localhost:8000/metrics`
- `POST http://localhost:8000/documents/ingest`
- `POST http://localhost:8000/rag/query`
- `POST http://localhost:8000/agent/run`
- `POST http://localhost:8000/agent/team/run`
- `GET http://localhost:8000/runs`
- `POST http://localhost:8000/evals/run`

## Switching to real model APIs

For providers that expose an OpenAI-compatible HTTP interface:

```env
MODEL_PROVIDER=openai_compatible
MODEL_ENDPOINT_MODE=responses
MODEL_BASE_URL=https://api.openai.com
MODEL_API_KEY=your_key
PRIMARY_MODEL_NAME=gpt-4.1-mini
```

If your provider only supports chat completions, set:

```env
MODEL_ENDPOINT_MODE=chat_completions
```

## Switching to real embeddings

```env
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_BASE_URL=https://api.openai.com
EMBEDDING_API_KEY=your_key
EMBEDDING_MODEL_NAME=text-embedding-3-small
```

## Switching to Qdrant

```env
VECTOR_STORE_BACKEND=qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION_NAME=knowledge_chunks
```

## Persisting run history

```env
RUN_STORE_BACKEND=sqlite
SQLITE_PATH=./data/agent_platform.db
```

## Enabling API auth

```env
API_AUTH_ENABLED=true
API_KEYS=demo-key,internal-key
```

Send the key in the `X-API-Key` request header.

## Structured logs and metrics

```env
LOG_LEVEL=INFO
```

The API now emits request-level structured logs, returns an `X-Request-ID` response header, exposes an operations summary at `/ops/overview`, and serves Prometheus-style metrics at `/metrics`.

## Production talking points

- Keep the parser, embedding, vector, rerank, model, and voice layers independently replaceable.
- Split OCR, embedding, rerank, and TTS into separate workers when GPU scheduling matters.
- Use `/ops/overview` and `/metrics` as the baseline observability surface before wiring logs and metrics into your external monitoring stack.
