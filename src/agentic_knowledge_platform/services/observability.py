from __future__ import annotations

from collections import Counter, deque
from threading import Lock
from time import time
from typing import Any


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


class MetricsCollector:
    REQUEST_BUCKETS = (50, 100, 250, 500, 1000, 2500, 5000)

    def __init__(self) -> None:
        self.started_at = time()
        self._lock = Lock()
        self._http_requests: Counter[tuple[str, str, str, str]] = Counter()
        self._http_latency_sum_ms: Counter[tuple[str, str]] = Counter()
        self._http_latency_max_ms: dict[tuple[str, str], int] = {}
        self._http_latency_buckets: Counter[tuple[str, str, str]] = Counter()
        self._pipeline_runs: Counter[tuple[str, str, str, str]] = Counter()
        self._pipeline_latency_sum_ms: Counter[tuple[str, str]] = Counter()
        self._pipeline_latency_max_ms: dict[tuple[str, str], int] = {}
        self._pipeline_citation_sum: Counter[tuple[str, str]] = Counter()
        self._pipeline_grounded_total: Counter[tuple[str, str]] = Counter()
        self._recent_requests: deque[dict[str, Any]] = deque(maxlen=25)

    def record_http(
        self,
        method: str,
        path: str,
        status_code: int,
        latency_ms: int,
        request_id: str,
    ) -> None:
        route_key = (method.upper(), path or "/")
        request_key = route_key + (str(status_code), f"{status_code // 100}xx")
        bounded_latency = max(latency_ms, 0)
        with self._lock:
            self._http_requests[request_key] += 1
            self._http_latency_sum_ms[route_key] += bounded_latency
            previous_max = self._http_latency_max_ms.get(route_key, 0)
            self._http_latency_max_ms[route_key] = max(previous_max, bounded_latency)
            for bucket in self.REQUEST_BUCKETS:
                if bounded_latency <= bucket:
                    self._http_latency_buckets[route_key + (str(bucket),)] += 1
            self._http_latency_buckets[route_key + ("+Inf",)] += 1
            self._recent_requests.appendleft(
                {
                    "request_id": request_id,
                    "method": route_key[0],
                    "path": route_key[1],
                    "status_code": status_code,
                    "latency_ms": bounded_latency,
                }
            )

    def record_pipeline_run(
        self,
        workflow: str,
        mode: str,
        grounded: bool,
        citation_count: int,
        latency_ms: int,
        voice_enabled: bool,
    ) -> None:
        stats_key = (workflow, mode)
        run_key = stats_key + (str(grounded).lower(), str(voice_enabled).lower())
        bounded_latency = max(latency_ms, 0)
        with self._lock:
            self._pipeline_runs[run_key] += 1
            self._pipeline_latency_sum_ms[stats_key] += bounded_latency
            previous_max = self._pipeline_latency_max_ms.get(stats_key, 0)
            self._pipeline_latency_max_ms[stats_key] = max(previous_max, bounded_latency)
            self._pipeline_citation_sum[stats_key] += max(citation_count, 0)
            if grounded:
                self._pipeline_grounded_total[stats_key] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            total_requests = sum(self._http_requests.values())
            routes = sorted({key[:2] for key in self._http_requests})
            route_stats = []
            for route_key in routes:
                request_count = sum(
                    count for key, count in self._http_requests.items() if key[:2] == route_key
                )
                error_count = sum(
                    count
                    for key, count in self._http_requests.items()
                    if key[:2] == route_key and not key[2].startswith("2")
                )
                latency_sum = self._http_latency_sum_ms.get(route_key, 0)
                route_stats.append(
                    {
                        "method": route_key[0],
                        "path": route_key[1],
                        "request_count": request_count,
                        "error_count": error_count,
                        "avg_latency_ms": round(latency_sum / request_count, 2) if request_count else 0.0,
                        "max_latency_ms": self._http_latency_max_ms.get(route_key, 0),
                    }
                )

            total_runs = sum(self._pipeline_runs.values())
            modes = sorted({key[1] for key in self._pipeline_runs})
            mode_stats = []
            for mode in modes:
                stat_keys = [key for key in self._pipeline_latency_sum_ms if key[1] == mode]
                run_count = sum(
                    count for key, count in self._pipeline_runs.items() if key[1] == mode
                )
                grounded_count = sum(
                    self._pipeline_grounded_total.get(stat_key, 0) for stat_key in stat_keys
                )
                citation_total = sum(
                    self._pipeline_citation_sum.get(stat_key, 0) for stat_key in stat_keys
                )
                latency_total = sum(
                    self._pipeline_latency_sum_ms.get(stat_key, 0) for stat_key in stat_keys
                )
                max_latency = max(
                    (self._pipeline_latency_max_ms.get(stat_key, 0) for stat_key in stat_keys),
                    default=0,
                )
                mode_stats.append(
                    {
                        "mode": mode,
                        "run_count": run_count,
                        "grounded_rate": round(grounded_count / run_count, 3) if run_count else 0.0,
                        "avg_citations": round(citation_total / run_count, 2) if run_count else 0.0,
                        "avg_latency_ms": round(latency_total / run_count, 2) if run_count else 0.0,
                        "max_latency_ms": max_latency,
                    }
                )

            return {
                "uptime_seconds": int(time() - self.started_at),
                "http": {
                    "total_requests": total_requests,
                    "routes": route_stats,
                    "recent_requests": list(self._recent_requests),
                },
                "pipelines": {
                    "total_runs": total_runs,
                    "by_mode": mode_stats,
                },
            }

    def render_prometheus(self) -> str:
        with self._lock:
            lines = [
                "# HELP akp_service_uptime_seconds Service uptime in seconds.",
                "# TYPE akp_service_uptime_seconds gauge",
                f"akp_service_uptime_seconds {int(time() - self.started_at)}",
                "# HELP akp_http_requests_total Total HTTP requests handled by the service.",
                "# TYPE akp_http_requests_total counter",
            ]
            for labels, count in sorted(self._http_requests.items()):
                method, path, status_code, status_family = labels
                lines.append(
                    "akp_http_requests_total"
                    f'{{method="{_escape_label(method)}",path="{_escape_label(path)}",'
                    f'status="{_escape_label(status_code)}",status_family="{_escape_label(status_family)}"}} {count}'
                )

            lines.extend(
                [
                    "# HELP akp_http_request_duration_ms_sum Total HTTP request latency in milliseconds.",
                    "# TYPE akp_http_request_duration_ms_sum counter",
                ]
            )
            for labels, total in sorted(self._http_latency_sum_ms.items()):
                method, path = labels
                lines.append(
                    "akp_http_request_duration_ms_sum"
                    f'{{method="{_escape_label(method)}",path="{_escape_label(path)}"}} {total}'
                )

            lines.extend(
                [
                    "# HELP akp_http_request_duration_ms_max Max HTTP request latency in milliseconds.",
                    "# TYPE akp_http_request_duration_ms_max gauge",
                ]
            )
            for labels, maximum in sorted(self._http_latency_max_ms.items()):
                method, path = labels
                lines.append(
                    "akp_http_request_duration_ms_max"
                    f'{{method="{_escape_label(method)}",path="{_escape_label(path)}"}} {maximum}'
                )

            lines.extend(
                [
                    "# HELP akp_http_request_duration_ms_bucket HTTP request latency histogram buckets.",
                    "# TYPE akp_http_request_duration_ms_bucket counter",
                ]
            )
            for labels, count in sorted(self._http_latency_buckets.items()):
                method, path, le_value = labels
                lines.append(
                    "akp_http_request_duration_ms_bucket"
                    f'{{method="{_escape_label(method)}",path="{_escape_label(path)}",le="{_escape_label(le_value)}"}} {count}'
                )

            lines.extend(
                [
                    "# HELP akp_pipeline_runs_total Total pipeline executions recorded by workflow and mode.",
                    "# TYPE akp_pipeline_runs_total counter",
                ]
            )
            for labels, count in sorted(self._pipeline_runs.items()):
                workflow, mode, grounded, voice_enabled = labels
                lines.append(
                    "akp_pipeline_runs_total"
                    f'{{workflow="{_escape_label(workflow)}",mode="{_escape_label(mode)}",'
                    f'grounded="{_escape_label(grounded)}",voice_enabled="{_escape_label(voice_enabled)}"}} {count}'
                )

            lines.extend(
                [
                    "# HELP akp_pipeline_latency_ms_sum Total pipeline latency in milliseconds.",
                    "# TYPE akp_pipeline_latency_ms_sum counter",
                ]
            )
            for labels, total in sorted(self._pipeline_latency_sum_ms.items()):
                workflow, mode = labels
                lines.append(
                    "akp_pipeline_latency_ms_sum"
                    f'{{workflow="{_escape_label(workflow)}",mode="{_escape_label(mode)}"}} {total}'
                )

            lines.extend(
                [
                    "# HELP akp_pipeline_latency_ms_max Max pipeline latency in milliseconds.",
                    "# TYPE akp_pipeline_latency_ms_max gauge",
                ]
            )
            for labels, maximum in sorted(self._pipeline_latency_max_ms.items()):
                workflow, mode = labels
                lines.append(
                    "akp_pipeline_latency_ms_max"
                    f'{{workflow="{_escape_label(workflow)}",mode="{_escape_label(mode)}"}} {maximum}'
                )

            lines.extend(
                [
                    "# HELP akp_pipeline_citations_total Total citations emitted by workflow and mode.",
                    "# TYPE akp_pipeline_citations_total counter",
                ]
            )
            for labels, total in sorted(self._pipeline_citation_sum.items()):
                workflow, mode = labels
                lines.append(
                    "akp_pipeline_citations_total"
                    f'{{workflow="{_escape_label(workflow)}",mode="{_escape_label(mode)}"}} {total}'
                )

            return "\n".join(lines) + "\n"
