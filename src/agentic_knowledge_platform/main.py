from __future__ import annotations

import json
import time
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentic_knowledge_platform.container import ServiceContainer, build_container
from agentic_knowledge_platform.core.logging import configure_logging, log_event
from agentic_knowledge_platform.core.serialization import to_dict
from agentic_knowledge_platform.demo_ui import load_demo_sample, render_demo_page
from agentic_knowledge_platform.services.local_corpus import bootstrap_local_corpus
from agentic_knowledge_platform.showcase_ui import render_showcase_page
from agentic_knowledge_platform.types import AgentRequest, DocumentIngestRequest

try:
    from fastapi import FastAPI, Header, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, StreamingResponse
    from fastapi.staticfiles import StaticFiles
except ModuleNotFoundError:  # pragma: no cover - expected in the current sandbox.
    FastAPI = None
    Header = None
    HTTPException = RuntimeError
    Request = None
    CORSMiddleware = None
    FileResponse = None
    HTMLResponse = None
    PlainTextResponse = None
    StreamingResponse = None
    StaticFiles = None


def _resolve_frontend_dist_dir(frontend_dist_dir: str) -> Path | None:
    configured = frontend_dist_dir.strip()
    if configured:
        candidate = Path(configured).expanduser().resolve()
        return candidate if candidate.exists() else None

    project_root = Path(__file__).resolve().parents[2]
    candidate = project_root / "frontend" / "dist"
    return candidate if candidate.exists() else None


def create_app(container: ServiceContainer | None = None):
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Run `pip install -e .` before starting the HTTP service.")

    services = container or build_container()
    app = FastAPI(title=services.settings.service_name, version="0.1.0")
    if CORSMiddleware is not None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://127.0.0.1:5173",
                "http://localhost:5173",
                "http://127.0.0.1:4173",
                "http://localhost:4173",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    logger = configure_logging(services.settings.log_level)
    allowed_api_keys = {
        item.strip() for item in services.settings.api_keys.split(",") if item.strip()
    }
    bootstrap_enabled = bool(
        services.settings.bootstrap_knowledge_paths.strip() or services.settings.bootstrap_snapshot_path.strip()
    )
    bootstrap_state: dict[str, Any] = {
        "status": "completed" if (bootstrap_enabled and services.knowledge_base.documents) else ("idle" if bootstrap_enabled else "disabled"),
        "ready": bool(services.knowledge_base.documents) if bootstrap_enabled else True,
        "error": None,
        "document_count": len(services.knowledge_base.list_documents(tenant_id=services.settings.bootstrap_tenant_id)),
        "vector_count": services.vector_store.size(),
    }
    bootstrap_lock = threading.Lock()
    bootstrap_thread: threading.Thread | None = None
    frontend_dist_dir = _resolve_frontend_dist_dir(services.settings.frontend_dist_dir)
    frontend_index = frontend_dist_dir / "index.html" if frontend_dist_dir else None
    frontend_assets_dir = frontend_dist_dir / "assets" if frontend_dist_dir else None

    if StaticFiles is not None and frontend_assets_dir and frontend_assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_assets_dir)), name="frontend-assets")

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        started_at = time.perf_counter()
        response = None
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            latency_ms = max(1, int((time.perf_counter() - started_at) * 1000))
            services.metrics.record_http(
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                latency_ms=latency_ms,
                request_id=request_id,
            )
            log_event(
                logger,
                "http_request_completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                latency_ms=latency_ms,
            )
            if response is not None:
                response.headers["X-Request-ID"] = request_id

    def require_api_key(x_api_key: str | None) -> None:
        if not services.settings.api_auth_enabled:
            return
        if not x_api_key or x_api_key not in allowed_api_keys:
            raise HTTPException(status_code=401, detail="invalid or missing API key")

    def record_pipeline(
        workflow: str,
        mode: str,
        grounded: bool,
        citation_count: int,
        latency_ms: int,
        voice_enabled: bool,
    ) -> None:
        services.metrics.record_pipeline_run(
            workflow=workflow,
            mode=mode,
            grounded=grounded,
            citation_count=citation_count,
            latency_ms=latency_ms,
            voice_enabled=voice_enabled,
        )
        log_event(
            logger,
            "pipeline_completed",
            workflow=workflow,
            mode=mode,
            grounded=grounded,
            citation_count=citation_count,
            latency_ms=latency_ms,
            voice_enabled=voice_enabled,
        )

    def refresh_bootstrap_snapshot() -> None:
        bootstrap_state["document_count"] = len(
            services.knowledge_base.list_documents(tenant_id=services.settings.bootstrap_tenant_id)
        )
        bootstrap_state["vector_count"] = services.vector_store.size()

    def start_background_bootstrap() -> None:
        nonlocal bootstrap_thread
        if not bootstrap_enabled or services.settings.bootstrap_mode != "background":
            return
        with bootstrap_lock:
            if bootstrap_state["status"] in {"running", "completed"}:
                return
            bootstrap_state.update({"status": "running", "ready": False, "error": None})

            def runner() -> None:
                try:
                    bootstrap_local_corpus(
                        knowledge_base=services.knowledge_base,
                        path_spec=services.settings.bootstrap_knowledge_paths,
                        tenant_id=services.settings.bootstrap_tenant_id,
                    )
                except Exception as exc:  # pragma: no cover - exercised in real deployment only.
                    bootstrap_state.update({"status": "failed", "ready": False, "error": str(exc)})
                    refresh_bootstrap_snapshot()
                    log_event(logger, "bootstrap_failed", error=str(exc))
                    return
                bootstrap_state.update({"status": "completed", "ready": True, "error": None})
                refresh_bootstrap_snapshot()
                log_event(
                    logger,
                    "bootstrap_completed",
                    document_count=bootstrap_state["document_count"],
                    vector_count=bootstrap_state["vector_count"],
                )

            bootstrap_thread = threading.Thread(
                target=runner,
                daemon=True,
                name="bootstrap-local-corpus",
            )
            bootstrap_thread.start()

    if bootstrap_enabled and services.settings.bootstrap_mode == "background":
        @app.on_event("startup")
        def startup_bootstrap() -> None:
            start_background_bootstrap()

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": services.settings.service_name,
            "documents": len(services.knowledge_base.documents),
            "vectors": services.vector_store.size(),
            "model_provider": services.settings.model_provider,
            "embedding_provider": services.settings.embedding_provider,
            "vector_store_backend": services.settings.vector_store_backend,
            "run_store_backend": services.settings.run_store_backend,
            "api_auth_enabled": services.settings.api_auth_enabled,
            "bootstrap_status": bootstrap_state["status"],
            "bootstrap_ready": bootstrap_state["ready"],
        }

    @app.get("/", response_class=HTMLResponse)
    def showcase_page():
        if FileResponse is not None and frontend_index and frontend_index.exists():
            return FileResponse(frontend_index)
        return HTMLResponse(render_showcase_page(services.settings.service_name))

    @app.get("/demo", response_class=HTMLResponse)
    def demo_page() -> HTMLResponse:
        return HTMLResponse(render_demo_page(services.settings.service_name))

    @app.post("/demo/bootstrap")
    @app.post("/showcase/bootstrap")
    def bootstrap_demo(
        force: bool = False,
    ) -> dict[str, Any]:
        if bootstrap_enabled:
            if force and services.settings.bootstrap_mode == "background":
                bootstrap_state.update({"status": "idle", "ready": False, "error": None})
            start_background_bootstrap()
            refresh_bootstrap_snapshot()
            return {
                "ready": bool(bootstrap_state["ready"]),
                "seeded": bootstrap_state["status"] == "completed",
                "status": bootstrap_state["status"],
                "document_count": bootstrap_state["document_count"],
                "vector_count": bootstrap_state["vector_count"],
                "error": bootstrap_state["error"],
            }
        sample = load_demo_sample()
        if force:
            fresh_container = build_container(services.settings)
            services.vector_store = fresh_container.vector_store
            services.knowledge_base.vector_store = fresh_container.vector_store
            services.knowledge_base.documents = fresh_container.knowledge_base.documents
            services.knowledge_base.chunks_by_document = fresh_container.knowledge_base.chunks_by_document
        existing = [
            item
            for item in services.knowledge_base.list_documents(tenant_id=sample["tenant_id"])
        ]
        if existing:
            return {
                "ready": True,
                "seeded": False,
                "document_count": len(existing),
            }
        request = DocumentIngestRequest(
            title=sample["title"],
            content=sample["content"],
            source=sample["source"],
            modality=sample["modality"],
            tenant_id=sample["tenant_id"],
        )
        result = services.knowledge_base.ingest(request)
        return {
            "ready": True,
            "seeded": True,
            "document_id": result.document.document_id,
            "chunk_count": len(result.chunks),
        }

    @app.get("/ops/overview")
    def ops_overview(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, Any]:
        require_api_key(x_api_key)
        return services.metrics.snapshot()

    @app.get("/metrics")
    def metrics(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> PlainTextResponse:
        require_api_key(x_api_key)
        return PlainTextResponse(services.metrics.render_prometheus(), media_type="text/plain; version=0.0.4")

    @app.get("/documents")
    def list_documents(
        tenant_id: str | None = None,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> list[dict[str, Any]]:
        require_api_key(x_api_key)
        return services.knowledge_base.list_documents(tenant_id=tenant_id)

    @app.post("/documents/ingest")
    def ingest_document(
        payload: dict[str, Any],
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, Any]:
        require_api_key(x_api_key)
        try:
            request = DocumentIngestRequest(**payload)
            result = services.knowledge_base.ingest(request)
            return {
                "document": to_dict(result.document),
                "chunk_count": len(result.chunks),
            }
        except TypeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/rag/query")
    def query_rag(
        payload: dict[str, Any],
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, Any]:
        require_api_key(x_api_key)
        question = str(payload.get("question", "")).strip()
        top_k = int(payload.get("top_k", services.settings.default_top_k))
        tenant_id = str(payload.get("tenant_id", "default"))
        if not question:
            raise HTTPException(status_code=400, detail="question is required")
        started_at = time.perf_counter()
        result = services.knowledge_base.answer(question, top_k, tenant_id=tenant_id)
        latency_ms = max(1, int((time.perf_counter() - started_at) * 1000))
        record_pipeline(
            workflow="rag_query",
            mode="rag",
            grounded=result.grounded,
            citation_count=len(result.citations),
            latency_ms=latency_ms,
            voice_enabled=False,
        )
        return to_dict(result)

    @app.post("/rag/query/stream")
    def query_rag_stream(
        payload: dict[str, Any],
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ):
        require_api_key(x_api_key)
        question = str(payload.get("question", "")).strip()
        top_k = int(payload.get("top_k", services.settings.default_top_k))
        tenant_id = str(payload.get("tenant_id", "default"))
        if not question:
            raise HTTPException(status_code=400, detail="question is required")

        def emit(event: dict[str, Any]) -> bytes:
            return (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8")

        def iterator():
            started_at = time.perf_counter()
            plan = services.knowledge_base.prepare_answer_plan(question, top_k=top_k, tenant_id=tenant_id)
            citations = to_dict(plan["citations"])
            hint = str(plan.get("hint", ""))
            preview_sections = [
                {"title": "结论", "body": ""},
                {
                    "title": "法条依据",
                    "body": "\n".join(
                        f"- {citation['section'] or citation['title']}：{citation['snippet']}" for citation in citations[:3]
                    )
                    if citations
                    else "当前未返回可展示的法条依据。",
                },
                {"title": "提示", "body": hint},
            ]
            yield emit(
                {
                    "type": "meta",
                    "result": {
                        "answer": "",
                        "grounded": bool(plan["grounded"]),
                        "citations": citations,
                        "answer_sections": preview_sections,
                        "reasoning": [],
                        "question_type": plan["question_type"],
                        "confidence": plan["confidence"],
                        "refusal_triggered": plan["refusal_triggered"],
                    },
                }
            )

            if plan["status"] != "grounded":
                result = services.knowledge_base.finalize_answer(plan)
                latency_ms = max(1, int((time.perf_counter() - started_at) * 1000))
                record_pipeline(
                    workflow="rag_query_stream",
                    mode="rag",
                    grounded=result.grounded,
                    citation_count=len(result.citations),
                    latency_ms=latency_ms,
                    voice_enabled=False,
                )
                yield emit({"type": "done", "result": to_dict(result)})
                return

            _, route, stream = services.model_router.stream_generate(plan["model_request"])
            full_answer = ""
            try:
                for chunk in stream:
                    full_answer += chunk
                    yield emit({"type": "delta", "delta": chunk})
            except Exception as exc:
                yield emit({"type": "error", "message": str(exc)})
                return

            result = services.knowledge_base.finalize_answer(plan, model_output=full_answer, route=route)
            latency_ms = max(1, int((time.perf_counter() - started_at) * 1000))
            record_pipeline(
                workflow="rag_query_stream",
                mode="rag",
                grounded=result.grounded,
                citation_count=len(result.citations),
                latency_ms=latency_ms,
                voice_enabled=False,
            )
            yield emit({"type": "done", "result": to_dict(result)})

        return StreamingResponse(iterator(), media_type="application/x-ndjson")

    @app.post("/agent/run")
    def run_agent(
        payload: dict[str, Any],
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, Any]:
        require_api_key(x_api_key)
        query = str(payload.get("query", "")).strip()
        if not query:
            raise HTTPException(status_code=400, detail="query is required")
        request = AgentRequest(
            query=query,
            session_id=str(payload.get("session_id", "default")),
            speak_response=bool(payload.get("speak_response", False)),
            tenant_id=str(payload.get("tenant_id", "default")),
        )
        started_at = time.perf_counter()
        response = services.agent.run(request)
        latency_ms = max(1, int((time.perf_counter() - started_at) * 1000))
        services.run_store.save(workflow="agent_run", request=request, response=response)
        record_pipeline(
            workflow="agent_run",
            mode=response.agent_mode,
            grounded=response.grounded,
            citation_count=len(response.citations),
            latency_ms=latency_ms,
            voice_enabled=response.voice_job is not None,
        )
        return to_dict(response)

    @app.post("/agent/auto/run")
    def run_auto_agent(
        payload: dict[str, Any],
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, Any]:
        require_api_key(x_api_key)
        query = str(payload.get("query", "")).strip()
        if not query:
            raise HTTPException(status_code=400, detail="query is required")
        request = AgentRequest(
            query=query,
            session_id=str(payload.get("session_id", "default")),
            speak_response=bool(payload.get("speak_response", False)),
            tenant_id=str(payload.get("tenant_id", "default")),
        )
        started_at = time.perf_counter()
        response = services.execution_router.run_auto(request)
        latency_ms = max(1, int((time.perf_counter() - started_at) * 1000))
        services.run_store.save(workflow="auto_agent_run", request=request, response=response)
        record_pipeline(
            workflow="auto_agent_run",
            mode=response.agent_mode,
            grounded=response.grounded,
            citation_count=len(response.citations),
            latency_ms=latency_ms,
            voice_enabled=response.voice_job is not None,
        )
        return to_dict(response)

    @app.post("/agent/team/run")
    def run_team_agent(
        payload: dict[str, Any],
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, Any]:
        require_api_key(x_api_key)
        query = str(payload.get("query", "")).strip()
        if not query:
            raise HTTPException(status_code=400, detail="query is required")
        request = AgentRequest(
            query=query,
            session_id=str(payload.get("session_id", "default")),
            speak_response=bool(payload.get("speak_response", False)),
            tenant_id=str(payload.get("tenant_id", "default")),
        )
        started_at = time.perf_counter()
        response = services.team_agent.run(request)
        latency_ms = max(1, int((time.perf_counter() - started_at) * 1000))
        services.run_store.save(workflow="team_agent_run", request=request, response=response)
        record_pipeline(
            workflow="team_agent_run",
            mode=response.agent_mode,
            grounded=response.grounded,
            citation_count=len(response.citations),
            latency_ms=latency_ms,
            voice_enabled=response.voice_job is not None,
        )
        return to_dict(response)

    @app.post("/voice/narrate")
    def narrate(
        payload: dict[str, Any],
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, Any]:
        require_api_key(x_api_key)
        text = str(payload.get("text", "")).strip()
        voice = str(payload.get("voice", "mentor"))
        if not text:
            raise HTTPException(status_code=400, detail="text is required")
        started_at = time.perf_counter()
        voice_job = services.voice_pipeline.narrate(text=text, voice=voice)
        latency_ms = max(1, int((time.perf_counter() - started_at) * 1000))
        record_pipeline(
            workflow="voice_narrate",
            mode="voice",
            grounded=True,
            citation_count=0,
            latency_ms=latency_ms,
            voice_enabled=True,
        )
        return to_dict(voice_job)

    @app.post("/workflow/demo")
    def workflow_demo(
        payload: dict[str, Any],
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, Any]:
        require_api_key(x_api_key)
        document_payload = payload.get("document") or {}
        question = str(payload.get("question", "")).strip()
        if not question:
            raise HTTPException(status_code=400, detail="question is required")
        try:
            document_request = DocumentIngestRequest(**document_payload)
        except TypeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        started_at = time.perf_counter()
        workflow_run = services.workflow.run(
            document_request=document_request,
            question=question,
            speak_response=bool(payload.get("speak_response", False)),
            agent_mode=str(payload.get("agent_mode", "single")),
            session_id=str(payload.get("session_id", "default")),
            tenant_id=str(payload.get("tenant_id", document_payload.get("tenant_id", "default"))),
        )
        latency_ms = max(1, int((time.perf_counter() - started_at) * 1000))
        record_pipeline(
            workflow="workflow_demo",
            mode=workflow_run.agent_response.agent_mode,
            grounded=workflow_run.agent_response.grounded,
            citation_count=len(workflow_run.agent_response.citations),
            latency_ms=latency_ms,
            voice_enabled=workflow_run.agent_response.voice_job is not None,
        )
        return to_dict(workflow_run)

    @app.get("/runs")
    def list_runs(
        limit: int = 20,
        tenant_id: str | None = None,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> list[dict[str, Any]]:
        require_api_key(x_api_key)
        return to_dict(services.run_store.list_runs(limit, tenant_id=tenant_id))

    @app.post("/evals/run")
    def run_evals(
        payload: dict[str, Any],
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, Any]:
        require_api_key(x_api_key)
        dataset_path = str(payload.get("dataset_path", "examples/eval_dataset.json"))
        return to_dict(services.evaluation_service.evaluate_from_file(dataset_path))

    return app
