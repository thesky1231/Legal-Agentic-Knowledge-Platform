from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.core.resilience import RetryPolicy, SlidingWindowRateLimiter
from agentic_knowledge_platform.services.model_router import ModelRouter, TemplateModelClient
from agentic_knowledge_platform.types import ModelRequest


class ModelRouterTests(unittest.TestCase):
    def test_fallback_when_primary_route_fails(self) -> None:
        router = ModelRouter(
            clients=[
                TemplateModelClient(
                    name="primary",
                    supported_tasks={"qa"},
                    persona="主模型",
                    fail_tasks={"qa"},
                ),
                TemplateModelClient(
                    name="backup",
                    supported_tasks={"qa"},
                    persona="备用模型",
                ),
            ],
            task_routes={"qa": ["primary", "backup"]},
            rate_limiter=SlidingWindowRateLimiter(limit=10, window_seconds=60),
            failure_threshold=1,
            recovery_timeout=60,
            retry_policy=RetryPolicy(max_attempts=1, base_delay_seconds=0.0),
        )

        response = router.generate(
            ModelRequest(
                task="qa",
                prompt="主模型失败时怎么处理",
                context_blocks=["问答优先走主模型，失败后 fallback 到备用模型。"],
            )
        )

        self.assertEqual(response.route, "backup")
        self.assertEqual(router.breaker_state("primary")["state"], "open")


if __name__ == "__main__":
    unittest.main()
