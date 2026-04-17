from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.services.observability import MetricsCollector


class ObservabilityTests(unittest.TestCase):
    def test_snapshot_and_prometheus_output_include_http_and_pipeline_stats(self) -> None:
        collector = MetricsCollector()
        collector.record_http(
            method="GET",
            path="/health",
            status_code=200,
            latency_ms=12,
            request_id="req-health",
        )
        collector.record_http(
            method="POST",
            path="/agent/run",
            status_code=500,
            latency_ms=212,
            request_id="req-agent",
        )
        collector.record_pipeline_run(
            workflow="agent_run",
            mode="single",
            grounded=True,
            citation_count=3,
            latency_ms=87,
            voice_enabled=False,
        )
        collector.record_pipeline_run(
            workflow="team_agent_run",
            mode="team",
            grounded=False,
            citation_count=1,
            latency_ms=143,
            voice_enabled=True,
        )

        snapshot = collector.snapshot()
        self.assertEqual(snapshot["http"]["total_requests"], 2)
        self.assertEqual(snapshot["pipelines"]["total_runs"], 2)
        modes = {item["mode"]: item for item in snapshot["pipelines"]["by_mode"]}
        self.assertEqual(modes["single"]["grounded_rate"], 1.0)
        self.assertEqual(modes["team"]["avg_citations"], 1.0)

        metrics_text = collector.render_prometheus()
        self.assertIn(
            'akp_http_requests_total{method="GET",path="/health",status="200",status_family="2xx"} 1',
            metrics_text,
        )
        self.assertIn(
            'akp_pipeline_runs_total{workflow="agent_run",mode="single",grounded="true",voice_enabled="false"} 1',
            metrics_text,
        )


if __name__ == "__main__":
    unittest.main()
