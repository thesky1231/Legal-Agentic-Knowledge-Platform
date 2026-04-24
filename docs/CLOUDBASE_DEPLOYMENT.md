# CloudBase Deployment

This project is now packaged for a single-service CloudBase Run deployment:

- FastAPI serves the backend APIs
- the built React frontend is served from the same container at `/`
- the service can bootstrap a fixed legal corpus at startup

## Recommended deployment mode

For this repository, the cleanest CloudBase path is:

1. deploy a single service with the repository Dockerfile
2. expose it as a `WEB` service
3. set the service port to `8000` or let CloudBase inject `PORT`
4. configure startup environment variables in the service console

Because the frontend is bundled into the image, you do not need a second static-site deployment just to show the product demo.

## Required environment variables

For a legal-demo deployment backed by your fixed corpus:

```env
SERVICE_NAME=Legal Agentic Knowledge Platform
FRONTEND_DIST_DIR=/app/frontend/dist

BOOTSTRAP_KNOWLEDGE_PATHS=/app/data/law.pdf
BOOTSTRAP_TENANT_ID=demo

MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL_NAME=qwen2.5:7b
OLLAMA_TEMPERATURE=0

RUN_STORE_BACKEND=memory
```

You can also start from the repository template:

```text
.env.cloudbase.example
```

If you are not running Ollama inside the same reachable network, switch back to:

```env
MODEL_PROVIDER=stub
```

or configure an external OpenAI-compatible provider instead.

## Two important deployment constraints

### 1. Your local Windows path will not exist in CloudBase

This will work locally:

```env
BOOTSTRAP_KNOWLEDGE_PATHS=E:\My_github\Legal-AI\data\law.pdf
```

But it will not work in CloudBase, because the container cannot read your local disk.

For CloudBase, move the corpus file into the repository and point to the in-container path instead:

```env
BOOTSTRAP_KNOWLEDGE_PATHS=/app/examples/legal/law.pdf
```

### 2. Your local Ollama service will not be reachable from CloudBase

This works on your own machine:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

But in CloudBase that address points to the container itself, not your PC.

So your first cloud deployment should usually use one of these:

- `MODEL_PROVIDER=stub` for a no-network demo
- `MODEL_PROVIDER=openai_compatible` for a real remote model API
- a separately deployed Ollama endpoint that CloudBase can actually reach

### 3. CloudBase local filesystem is temporary

For CloudBase Run, container local storage is temporary and cleared when the instance is reclaimed.

That means:

- `RUN_STORE_BACKEND=memory` is the safest first deployment mode
- if you use SQLite in CloudBase, treat it as temporary demo state only
- long-lived files should go to COS or another external storage service

## Corpus strategy

This service treats the legal corpus as fixed startup data, not as a user-facing upload flow.

- `.pdf` and `.txt` startup files use the legacy article-level legal parsing logic
- `.md` startup files use the markdown parser
- the knowledge base is built when the container starts

## If you want to ship `law.pdf` inside the image

Place the file somewhere in the repository before building, for example:

```text
examples/legal/law.pdf
```

Then set:

```env
BOOTSTRAP_KNOWLEDGE_PATHS=/app/examples/legal/law.pdf
```

## CloudBase console checklist

- Access type: `WEB`
- Port: `8000`
- CPU: `0.5` to `1`
- Memory: `1GB` to `2GB`
- Minimum instances: `0` for demo, `1` if you want to reduce cold starts
- Maximum instances: `2` to `5` for a personal demo

## What the deployed service exposes

- `GET /` : product frontend
- `GET /health` : health check
- `POST /showcase/bootstrap` : frontend bootstrap action
- `POST /rag/query`
- `POST /agent/run`
- `POST /agent/team/run`

## Notes

- If you deploy with the current Dockerfile, the frontend is built during image build.
- The runtime image now includes `pypdf`, so startup corpus bootstrapping can read legal PDF files.
- If you keep `VITE_API_BASE_URL` empty during production build, the frontend calls the backend on the same origin.
