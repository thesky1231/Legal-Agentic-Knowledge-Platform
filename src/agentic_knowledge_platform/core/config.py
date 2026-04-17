from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class Settings:
    service_name: str = os.getenv("SERVICE_NAME", "Agentic Knowledge Platform")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "96"))
    default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "4"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "450"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "80"))
    grounded_threshold: float = float(os.getenv("GROUNDED_THRESHOLD", "0.22"))
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    circuit_breaker_failures: int = int(os.getenv("CIRCUIT_BREAKER_FAILURES", "2"))
    circuit_breaker_recovery_seconds: int = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_SECONDS", "15"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    model_provider: str = os.getenv("MODEL_PROVIDER", "stub")
    model_endpoint_mode: str = os.getenv("MODEL_ENDPOINT_MODE", "responses")
    model_base_url: str = os.getenv("MODEL_BASE_URL", "https://api.openai.com")
    model_api_key: str = os.getenv("MODEL_API_KEY", "")
    primary_model_name: str = os.getenv("PRIMARY_MODEL_NAME", "gpt-4.1-mini")
    primary_model_label: str = os.getenv("PRIMARY_MODEL_LABEL", "Primary Model")
    backup_model_label: str = os.getenv("BACKUP_MODEL_LABEL", "Fallback Model")
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "hash")
    embedding_base_url: str = os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com")
    embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", "")
    embedding_model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
    vector_store_backend: str = os.getenv("VECTOR_STORE_BACKEND", "memory")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_collection_name: str = os.getenv("QDRANT_COLLECTION_NAME", "knowledge_chunks")
    run_store_backend: str = os.getenv("RUN_STORE_BACKEND", "memory")
    sqlite_path: str = os.getenv("SQLITE_PATH", "./data/agent_platform.db")
    api_auth_enabled: bool = os.getenv("API_AUTH_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    api_keys: str = os.getenv("API_KEYS", "demo-key")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
