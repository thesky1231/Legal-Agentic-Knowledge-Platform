from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.services.openai_compatible import (
    OpenAICompatibleEmbeddingService,
    OpenAICompatibleModelClient,
)
from agentic_knowledge_platform.services.ollama import OllamaModelClient
from agentic_knowledge_platform.services.vector_store import QdrantRestVectorStore
from agentic_knowledge_platform.types import ChunkRecord, ModelRequest


class FakeHttpClient:
    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def post(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        self.calls.append(("POST", path, payload))
        return self.responses.pop(0)

    def put(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        self.calls.append(("PUT", path, payload))
        return self.responses.pop(0) if self.responses else {}


class FakeQdrantStore(QdrantRestVectorStore):
    def __init__(self) -> None:
        self.collection_name = "knowledge_chunks"
        self.vector_size = 4
        self.cached_size = 0
        self.http = FakeHttpClient([])

    def _ensure_collection(self) -> None:
        return None


class RemoteAdapterTests(unittest.TestCase):
    def test_ollama_model_client_reads_generate_response(self) -> None:
        client = OllamaModelClient(
            name="primary-router",
            model="qwen2.5:7b",
            base_url="http://localhost:11434",
            supported_tasks={"qa"},
            timeout_seconds=5,
            temperature=0.0,
        )
        client.http = FakeHttpClient([{"response": "Grounded answer from ollama."}])

        output = client.generate(ModelRequest(task="qa", prompt="How is fallback handled?", context_blocks=["Use citations."]))

        self.assertEqual(output, "Grounded answer from ollama.")
        self.assertEqual(client.http.calls[0][1], "/api/generate")
        self.assertEqual(client.http.calls[0][2]["model"], "qwen2.5:7b")

    def test_openai_compatible_model_client_parses_responses_output(self) -> None:
        client = OpenAICompatibleModelClient(
            name="primary-router",
            model="gpt-test",
            base_url="https://api.example.com",
            api_key="secret",
            endpoint_mode="responses",
            supported_tasks={"qa"},
            timeout_seconds=5,
        )
        client.http = FakeHttpClient(
            [
                {
                    "output": [
                        {
                            "content": [
                                {"type": "output_text", "text": "Grounded answer from remote model."}
                            ]
                        }
                    ]
                }
            ]
        )

        output = client.generate(ModelRequest(task="qa", prompt="What is the fallback path?", context_blocks=["Use backup model."]))

        self.assertEqual(output, "Grounded answer from remote model.")
        self.assertEqual(client.http.calls[0][1], "/v1/responses")

    def test_openai_compatible_embedding_service_reads_vectors(self) -> None:
        service = OpenAICompatibleEmbeddingService(
            base_url="https://api.example.com",
            api_key="secret",
            model="text-embedding-3-small",
            dimensions=3,
            timeout_seconds=5,
        )
        service.http = FakeHttpClient([{"data": [{"embedding": [0.1, 0.2, 0.3]}]}])

        vector = service.embed("hello")

        self.assertEqual(vector, [0.1, 0.2, 0.3])
        self.assertEqual(service.http.calls[0][1], "/v1/embeddings")

    def test_qdrant_store_maps_search_payload_back_to_chunks(self) -> None:
        store = FakeQdrantStore()
        store.http.responses.append(
            {
                "result": {
                    "points": [
                        {
                            "id": "chunk-1",
                            "score": 0.88,
                            "payload": {
                                "chunk_id": "chunk-1",
                                "document_id": "doc-1",
                                "title": "Handbook",
                                "section": "Fallback",
                                "content": "Switch to backup router on failure.",
                                "source": "unit",
                                "metadata": {"tenant": "demo"},
                                "token_count": 7,
                            },
                        }
                    ]
                }
            }
        )

        hits = store.search([0.2, 0.1, 0.3, 0.4], top_k=1)

        self.assertEqual(len(hits), 1)
        self.assertAlmostEqual(hits[0][0], 0.88)
        self.assertEqual(hits[0][1].chunk.section, "Fallback")
        self.assertEqual(store.http.calls[0][1], "/collections/knowledge_chunks/points/query")

    def test_qdrant_store_upsert_uses_chunk_payload(self) -> None:
        store = FakeQdrantStore()
        chunk = ChunkRecord(
            chunk_id="chunk-1",
            document_id="doc-1",
            title="Handbook",
            section="Routing",
            content="Fallback to backup model.",
            source="unit",
            metadata={"tenant": "demo"},
            token_count=5,
        )

        store.upsert([chunk], [[0.1, 0.2, 0.3, 0.4]])

        method, path, payload = store.http.calls[0]
        self.assertEqual(method, "PUT")
        self.assertEqual(path, "/collections/knowledge_chunks/points")
        self.assertEqual(payload["points"][0]["payload"]["section"], "Routing")


if __name__ == "__main__":
    unittest.main()
