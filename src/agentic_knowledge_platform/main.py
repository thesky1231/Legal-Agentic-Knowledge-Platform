from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from agentic_knowledge_platform.container import ServiceContainer, build_container
from agentic_knowledge_platform.core.logging import configure_logging, log_event
from agentic_knowledge_platform.core.serialization import to_dict
from agentic_knowledge_platform.types import AgentRequest, DocumentIngestRequest

try:
    from fastapi import FastAPI, Header, HTTPException, Request
    from fastapi.responses import PlainTextResponse
except ModuleNotFoundError:  # pragma: no cover - expected in the current sandbox.
    FastAPI = None
    Header = None
    HTTPException = RuntimeError
    Request = None
    PlainTextResponse = None


def create_app(container: ServiceContainer | None = None):
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Run `pip install -e .` before starting the HTTP service.")

    services = container or build_container()
    app = FastAPI(title=services.settings.service_name, version="0.1.0")
    logger = configure_logging(services.settings.log_level)
    allowed_api_keys = {
        item.strip() for item in services.settings.api_keys.split(",") if item.strip()
    }

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
