from __future__ import annotations

from dataclasses import dataclass

from agentic_knowledge_platform.agents.single import ReActAgent
from agentic_knowledge_platform.agents.team import CollaborativeTeamAgent, ReviewAgent
from agentic_knowledge_platform.core.config import Settings, get_settings
from agentic_knowledge_platform.core.resilience import RetryPolicy, SlidingWindowRateLimiter
from agentic_knowledge_platform.services.chunking import StructureAwareChunker
from agentic_knowledge_platform.services.bootstrap_snapshot import load_snapshot_into_knowledge_base
from agentic_knowledge_platform.services.embeddings import HashEmbeddingService
from agentic_knowledge_platform.services.evaluation import EvaluationService
from agentic_knowledge_platform.services.execution_router import ExecutionRouter
from agentic_knowledge_platform.services.model_router import ModelRouter, TemplateModelClient
from agentic_knowledge_platform.services.observability import MetricsCollector
from agentic_knowledge_platform.services.ollama import OllamaModelClient
from agentic_knowledge_platform.services.openai_compatible import (
    EmbeddingService,
    ModelClient,
    OpenAICompatibleEmbeddingService,
    OpenAICompatibleModelClient,
)
from agentic_knowledge_platform.services.knowledge_base import KnowledgeBaseService, LexicalReranker
from agentic_knowledge_platform.services.local_corpus import bootstrap_local_corpus
from agentic_knowledge_platform.services.parsing import MultiModalDocumentParser
from agentic_knowledge_platform.services.run_store import InMemoryRunStore, RunStore, SQLiteRunStore
from agentic_knowledge_platform.services.vector_store import InMemoryVectorStore, QdrantRestVectorStore, VectorStore
from agentic_knowledge_platform.services.voice import StubAvatarRenderer, StubSpeechSynthesizer, VoicePipeline
from agentic_knowledge_platform.workflows.tutor import TutoringWorkflow


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    parser: MultiModalDocumentParser
    chunker: StructureAwareChunker
    embeddings: EmbeddingService
    vector_store: VectorStore
    model_router: ModelRouter
    knowledge_base: KnowledgeBaseService
    voice_pipeline: VoicePipeline
    agent: ReActAgent
    team_agent: CollaborativeTeamAgent
    execution_router: ExecutionRouter
    run_store: RunStore
    metrics: MetricsCollector
    evaluation_service: EvaluationService
    workflow: TutoringWorkflow


def build_container(settings: Settings | None = None) -> ServiceContainer:
    active_settings = settings or get_settings()
    parser = MultiModalDocumentParser()
    chunker = StructureAwareChunker(
        max_chars=active_settings.chunk_size,
        overlap=active_settings.chunk_overlap,
    )
    embeddings = _build_embeddings(active_settings)
    vector_store = _build_vector_store(active_settings)
    rate_limiter = SlidingWindowRateLimiter(limit=active_settings.rate_limit_per_minute, window_seconds=60.0)
    model_router = ModelRouter(
        clients=_build_model_clients(active_settings),
        task_routes={
            "summary": ["primary-router", "backup-router"],
            "qa": ["primary-router", "backup-router"],
            "speech_script": ["backup-router"],
        },
        rate_limiter=rate_limiter,
        failure_threshold=active_settings.circuit_breaker_failures,
        recovery_timeout=active_settings.circuit_breaker_recovery_seconds,
        retry_policy=RetryPolicy(max_attempts=2, base_delay_seconds=0.01),
    )
    knowledge_base = KnowledgeBaseService(
        parser=parser,
        chunker=chunker,
        embeddings=embeddings,
        vector_store=vector_store,
        reranker=LexicalReranker(),
        model_router=model_router,
        grounded_threshold=active_settings.grounded_threshold,
        default_top_k=active_settings.default_top_k,
        embedding_batch_size=active_settings.embedding_batch_size,
    )
    snapshot_loaded = False
    if active_settings.bootstrap_snapshot_path.strip():
        load_snapshot_into_knowledge_base(
            knowledge_base=knowledge_base,
            vector_store=vector_store,
            path=active_settings.bootstrap_snapshot_path,
            embedding_batch_size=active_settings.embedding_batch_size,
        )
        snapshot_loaded = True
    if (
        not snapshot_loaded
        and active_settings.bootstrap_knowledge_paths.strip()
        and active_settings.bootstrap_mode == "sync"
    ):
        bootstrap_local_corpus(
            knowledge_base=knowledge_base,
            path_spec=active_settings.bootstrap_knowledge_paths,
            tenant_id=active_settings.bootstrap_tenant_id,
        )
    voice_pipeline = VoicePipeline(
        model_router=model_router,
        synthesizer=StubSpeechSynthesizer(),
        avatar_renderer=StubAvatarRenderer(),
    )
    agent = ReActAgent(knowledge_base=knowledge_base, voice_pipeline=voice_pipeline)
    team_agent = CollaborativeTeamAgent(
        react_agent=agent,
        voice_pipeline=voice_pipeline,
        reviewer=ReviewAgent(),
    )
    execution_router = ExecutionRouter(
        knowledge_base=knowledge_base,
        single_agent=agent,
        team_agent=team_agent,
        question_policy=knowledge_base.question_policy,
    )
    run_store = _build_run_store(active_settings)
    metrics = MetricsCollector()
    evaluation_service = EvaluationService(agent=agent, team_agent=team_agent)
    workflow = TutoringWorkflow(
        knowledge_base=knowledge_base,
        agent=agent,
        team_agent=team_agent,
        run_store=run_store,
    )
    return ServiceContainer(
        settings=active_settings,
        parser=parser,
        chunker=chunker,
        embeddings=embeddings,
        vector_store=vector_store,
        model_router=model_router,
        knowledge_base=knowledge_base,
        voice_pipeline=voice_pipeline,
        agent=agent,
        team_agent=team_agent,
        execution_router=execution_router,
        run_store=run_store,
        metrics=metrics,
        evaluation_service=evaluation_service,
        workflow=workflow,
    )


def _build_embeddings(settings: Settings) -> EmbeddingService:
    if settings.embedding_provider == "openai_compatible":
        if not settings.embedding_api_key:
            raise ValueError("EMBEDDING_API_KEY is required when EMBEDDING_PROVIDER=openai_compatible")
        return OpenAICompatibleEmbeddingService(
            base_url=settings.embedding_base_url,
            api_key=settings.embedding_api_key,
            model=settings.embedding_model_name,
            dimensions=settings.embedding_dimensions,
            timeout_seconds=settings.request_timeout_seconds,
        )
    return HashEmbeddingService(dimensions=settings.embedding_dimensions)


def _build_vector_store(settings: Settings) -> VectorStore:
    if settings.vector_store_backend == "qdrant":
        return QdrantRestVectorStore(
            base_url=settings.qdrant_url,
            collection_name=settings.qdrant_collection_name,
            vector_size=settings.embedding_dimensions,
            api_key=settings.qdrant_api_key,
            timeout_seconds=settings.request_timeout_seconds,
        )
    return InMemoryVectorStore()


def _build_model_clients(settings: Settings) -> list[ModelClient]:
    if settings.model_provider == "openai_compatible":
        if not settings.model_api_key:
            raise ValueError("MODEL_API_KEY is required when MODEL_PROVIDER=openai_compatible")
        primary = OpenAICompatibleModelClient(
            name="primary-router",
            model=settings.primary_model_name,
            base_url=settings.model_base_url,
            api_key=settings.model_api_key,
            endpoint_mode=settings.model_endpoint_mode,
            supported_tasks={"summary", "qa"},
            timeout_seconds=settings.request_timeout_seconds,
        )
    elif settings.model_provider == "ollama":
        primary = OllamaModelClient(
            name="primary-router",
            model=settings.ollama_model_name,
            base_url=settings.ollama_base_url,
            supported_tasks={"summary", "qa"},
            timeout_seconds=settings.request_timeout_seconds,
            temperature=settings.ollama_temperature,
            keep_alive=settings.ollama_keep_alive,
        )
    else:
        primary = TemplateModelClient(
            name="primary-router",
            supported_tasks={"summary", "qa"},
            persona=settings.primary_model_label,
        )

    backup = TemplateModelClient(
        name="backup-router",
        supported_tasks={"summary", "qa", "speech_script"},
        persona=settings.backup_model_label,
    )
    return [primary, backup]


def _build_run_store(settings: Settings) -> RunStore:
    if settings.run_store_backend == "sqlite":
        return SQLiteRunStore(db_path=settings.sqlite_path)
    return InMemoryRunStore()
