from __future__ import annotations

import json
from dataclasses import dataclass
from collections.abc import Iterator
from urllib import error, parse, request


@dataclass(slots=True)
class JsonHttpClient:
    base_url: str
    timeout_seconds: int = 20
    default_headers: dict[str, str] | None = None

    def post(self, path: str, payload: dict[str, object], headers: dict[str, str] | None = None) -> dict[str, object]:
        return self._request_json("POST", path, payload=payload, headers=headers)

    def put(self, path: str, payload: dict[str, object], headers: dict[str, str] | None = None) -> dict[str, object]:
        return self._request_json("PUT", path, payload=payload, headers=headers)

    def stream(self, path: str, payload: dict[str, object], headers: dict[str, str] | None = None) -> Iterator[dict[str, object]]:
        return self._request_sse("POST", path, payload=payload, headers=headers)

    def _request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        merged_headers = {"Content-Type": "application/json"}
        if self.default_headers:
            merged_headers.update(self.default_headers)
        if headers:
            merged_headers.update(headers)
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        target = parse.urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
        req = request.Request(target, data=body, headers=merged_headers, method=method)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                if not raw.strip():
                    return {}
                return json.loads(raw)
        except error.HTTPError as exc:  # pragma: no cover - exercised only with real remote backends.
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"http {exc.code} calling {target}: {detail}") from exc
        except error.URLError as exc:  # pragma: no cover - exercised only with real remote backends.
            raise RuntimeError(f"network error calling {target}: {exc.reason}") from exc

    def _request_sse(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Iterator[dict[str, object]]:
        merged_headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        if self.default_headers:
            merged_headers.update(self.default_headers)
        if headers:
            merged_headers.update(headers)
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        target = parse.urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
        req = request.Request(target, data=body, headers=merged_headers, method=method)

        def iterator() -> Iterator[dict[str, object]]:
            try:
                with request.urlopen(req, timeout=self.timeout_seconds) as response:
                    data_lines: list[str] = []
                    for raw_line in response:
                        line = raw_line.decode("utf-8", errors="replace").strip()
                        if not line:
                            if data_lines:
                                payload_text = "\n".join(data_lines).strip()
                                data_lines.clear()
                                if payload_text == "[DONE]":
                                    break
                                if payload_text:
                                    yield json.loads(payload_text)
                            continue
                        if line.startswith("data:"):
                            data_lines.append(line[5:].strip())
                    if data_lines:
                        payload_text = "\n".join(data_lines).strip()
                        if payload_text and payload_text != "[DONE]":
                            yield json.loads(payload_text)
            except error.HTTPError as exc:  # pragma: no cover - exercised only with real remote backends.
                detail = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"http {exc.code} calling {target}: {detail}") from exc
            except error.URLError as exc:  # pragma: no cover - exercised only with real remote backends.
                raise RuntimeError(f"network error calling {target}: {exc.reason}") from exc

        return iterator()
