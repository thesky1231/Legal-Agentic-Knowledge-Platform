from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.services.ollama import OllamaModelClient
from agentic_knowledge_platform.services.openai_compatible import (
    OpenAICompatibleEmbeddingService,
    OpenAICompatibleModelClient,
)
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

    def stream(self, path: str, payload: dict[str, object]):
        self.calls.append(("STREAM", path, payload))
        return iter(self.responses.pop(0))


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

        output = client.generate(
            ModelRequest(task="qa", prompt="How is fallback handled?", context_blocks=["Use citations."])
        )

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

        output = client.generate(
            ModelRequest(
                task="qa",
                prompt="robbery vs snatching",
                context_blocks=[
                    "Article 263: robbery uses violence or coercion to take property.",
                    "Article 267: snatching publicly seizes property.",
                ],
                metadata={"question_type": "confusing", "citation_count": "2"},
            )
        )

        self.assertEqual(output, "Grounded answer from remote model.")
        self.assertEqual(client.http.calls[0][1], "/v1/responses")
        prompt = client.http.calls[0][2]["input"]
        self.assertIn("Answer Composer v2", prompt)
        self.assertIn("Question type: confusing", prompt)
        self.assertIn("do_not_dump_statutes", prompt)
        self.assertIn("do_not_use_general_legal_knowledge", prompt)
        self.assertIn("Article 263", prompt)
        self.assertNotIn("当前知识库没有检索到足以回答该问题的依据", prompt)

    def test_openai_compatible_chat_prompt_uses_conservative_temperature(self) -> None:
        client = OpenAICompatibleModelClient(
            name="primary-router",
            model="qwen-plus",
            base_url="https://api.example.com",
            api_key="secret",
            endpoint_mode="chat_completions",
            supported_tasks={"qa"},
            timeout_seconds=5,
        )
        client.http = FakeHttpClient([{"choices": [{"message": {"content": "conservative answer"}}]}])

        client.generate(
            ModelRequest(
                task="qa",
                prompt="company annual leave days?",
                context_blocks=["Article 272: misappropriation of funds."],
                metadata={"question_type": "direct_answer", "citation_count": "1"},
            )
        )

        _, path, payload = client.http.calls[0]
        self.assertEqual(path, "/v1/chat/completions")
        self.assertEqual(payload["temperature"], 0.0)
        user_prompt = payload["messages"][1]["content"]
        self.assertIn("Answer Composer v2", user_prompt)
        self.assertIn("do_not_answer_from_weak_evidence", user_prompt)
        self.assertIn("do_not_use_general_legal_knowledge", user_prompt)

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

    def test_openai_compatible_model_client_streams_responses_delta(self) -> None:
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
                [
                    {"type": "response.output_text.delta", "delta": "robbery"},
                    {"type": "response.output_text.delta", "delta": " involves coercion."},
                ]
            ]
        )

        chunks = list(
            client.stream_generate(
                ModelRequest(task="qa", prompt="What is robbery?", context_blocks=["Article text"])
            )
        )

        self.assertEqual(["robbery", " involves coercion."], chunks)
        self.assertEqual(client.http.calls[0][0], "STREAM")
        self.assertEqual(client.http.calls[0][1], "/v1/responses")

    def test_openai_compatible_embedding_service_splits_large_batches(self) -> None:
        service = OpenAICompatibleEmbeddingService(
            base_url="https://api.example.com",
            api_key="secret",
            model="text-embedding-3-small",
            dimensions=3,
            max_batch_size=10,
            timeout_seconds=5,
        )
        service.http = FakeHttpClient(
            [
                {"data": [{"embedding": [float(index), 0.0, 1.0]} for index in range(10)]},
                {"data": [{"embedding": [10.0, 0.0, 1.0]}, {"embedding": [11.0, 0.0, 1.0]}]},
            ]
        )

        vectors = service.batch_embed([f"text-{index}" for index in range(12)])

        self.assertEqual(12, len(vectors))
        self.assertEqual(2, len(service.http.calls))
        self.assertEqual(10, len(service.http.calls[0][2]["input"]))
        self.assertEqual(2, len(service.http.calls[1][2]["input"]))

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
