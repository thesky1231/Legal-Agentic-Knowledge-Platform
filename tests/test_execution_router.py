from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - depends on local test environment.
    TestClient = None

from agentic_knowledge_platform.container import build_container
from agentic_knowledge_platform.main import create_app
from agentic_knowledge_platform.services.execution_router import ExecutionRouter
from agentic_knowledge_platform.services.query_policy import QuestionPolicyService
from agentic_knowledge_platform.types import (
    AgentRequest,
    AgentResponse,
    AgentStep,
    AnswerResult,
    DocumentIngestRequest,
)


LEGAL_CORPUS = """
# 刑事法律知识

## 盗窃罪构成要件
盗窃罪通常围绕非法占有目的、秘密窃取行为、公私财物对象以及数额或情节要求展开。
构成要件问题应结合行为方式、财物属性、主观目的和证据材料进行说明，并提供相应引用。

## 正当防卫定义
正当防卫是为了使国家、公共利益、本人或者他人的人身、财产和其他权利免受正在进行的不法侵害，
对不法侵害人采取制止行为，造成损害的，依法不负刑事责任。定义类问题应优先说明法律概念和适用边界。

## 抢劫罪和抢夺罪的区别
抢劫罪通常以暴力、胁迫或者其他足以压制被害人反抗的方法取得财物，行为同时侵犯财产法益和人身安全。
抢夺罪通常表现为乘人不备、公然夺取财物，一般不以暴力压制反抗为核心。比较二者时，应重点关注行为方式、暴力胁迫程度、保护法益和法条适用边界。

## 威胁后拿走财物的判断
如果行为人先威胁他人，随后拿走财物，应当结合威胁是否足以压制反抗、取财行为是否当场完成、
行为人与被害人的具体互动以及证据链完整程度判断罪名，不能仅凭一句话直接下确定性结论。
"""


class BadKnowledgeBase:
    def answer(self, question: str, top_k: int | None = None, tenant_id: str | None = None) -> AnswerResult:
        return AnswerResult(
            answer="证据不足。",
            grounded=False,
            citations=[],
            confidence="low",
            refusal_triggered=True,
        )


class FakeSingleAgent:
    def run(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            answer="single agent fallback",
            grounded=False,
            citations=[],
            steps=[
                AgentStep(
                    index=1,
                    agent="react-agent",
                    thought="Fallback after weak RAG result.",
                    action="answer_with_citations",
                    observation="grounded=False",
                )
            ],
            agent_mode="single",
            confidence="low",
            refusal_triggered=True,
        )


class FakeTeamAgent:
    def run(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            answer="team fallback",
            grounded=False,
            citations=[],
            steps=[],
            agent_mode="team",
            confidence="low",
            refusal_triggered=True,
        )


class ExecutionRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.container = build_container()
        self.container.knowledge_base.ingest(
            DocumentIngestRequest(
                title="刑事法律知识",
                content=LEGAL_CORPUS,
                source="unit",
                modality="markdown",
                tenant_id="demo",
            )
        )

    def test_direct_answer_auto_uses_rag_when_quality_is_good(self) -> None:
        response = self.container.execution_router.run_auto(
            AgentRequest(query="盗窃罪的构成要件是什么？", tenant_id="demo")
        )

        self.assertEqual(response.agent_mode, "auto_rag")
        self.assertEqual(response.question_type, "direct_answer")
        self.assertTrue(response.grounded)
        self.assertTrue(any(step.agent == "router-agent" for step in response.steps))
        self.assertTrue(any("model_route=" in step.observation for step in response.steps))
        self.assertTrue(any("model_error=" in step.observation for step in response.steps))

    def test_definition_auto_uses_rag_or_single_agent(self) -> None:
        response = self.container.execution_router.run_auto(
            AgentRequest(query="什么是正当防卫？", tenant_id="demo")
        )

        self.assertEqual(response.question_type, "definition")
        self.assertIn(response.agent_mode, {"auto_rag", "auto_single"})
        self.assertTrue(any(step.agent == "router-agent" for step in response.steps))

    def test_confusing_auto_uses_team_agent(self) -> None:
        response = self.container.execution_router.run_auto(
            AgentRequest(query="抢劫罪和抢夺罪有什么区别？", tenant_id="demo")
        )

        self.assertEqual(response.agent_mode, "auto_team")
        self.assertEqual(response.question_type, "confusing")
        self.assertTrue(any(step.agent == "router-agent" for step in response.steps))
        self.assertTrue(any(step.agent == "review-agent" for step in response.steps))

    def test_complex_reasoning_auto_uses_team_agent(self) -> None:
        response = self.container.execution_router.run_auto(
            AgentRequest(query="如果行为人先威胁后拿走财物，应当如何判断罪名？", tenant_id="demo")
        )

        self.assertEqual(response.agent_mode, "auto_team")
        self.assertEqual(response.question_type, "complex_reasoning")

    def test_weak_rag_result_escalates_to_single_agent(self) -> None:
        router = ExecutionRouter(
            knowledge_base=BadKnowledgeBase(),
            single_agent=FakeSingleAgent(),
            team_agent=FakeTeamAgent(),
            question_policy=QuestionPolicyService(),
        )

        response = router.run_auto(AgentRequest(query="盗窃罪的构成要件包括哪些？", tenant_id="demo"))

        self.assertEqual(response.agent_mode, "auto_single")
        self.assertTrue(any(step.action == "escalate" for step in response.steps))

    @unittest.skipIf(TestClient is None, "FastAPI test client is not available")
    def test_auto_endpoint_returns_unified_agent_response(self) -> None:
        app = create_app(self.container)
        client = TestClient(app)

        response = client.post(
            "/agent/auto/run",
            json={"query": "盗窃罪的构成要件是什么？", "tenant_id": "demo"},
        )
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("auto", payload["agent_mode"])
        self.assertIn("steps", payload)
        self.assertTrue(any(step["agent"] == "router-agent" for step in payload["steps"]))

    @unittest.skipIf(TestClient is None, "FastAPI test client is not available")
    def test_health_exposes_model_diagnostics_without_secrets(self) -> None:
        app = create_app(self.container)
        client = TestClient(app)

        response = client.get("/health")
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("model_endpoint_mode", payload)
        self.assertIn("primary_model_name", payload)
        self.assertIn("model_api_key_configured", payload)
        self.assertIn("model_clients", payload)
        self.assertTrue(any(client["name"] == "primary-router" for client in payload["model_clients"]))
        self.assertTrue(all("last_error" in client["breaker"] for client in payload["model_clients"]))
        self.assertNotIn("model_api_key", payload)


if __name__ == "__main__":
    unittest.main()
