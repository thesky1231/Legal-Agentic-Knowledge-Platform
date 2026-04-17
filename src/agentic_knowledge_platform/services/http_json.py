from __future__ import annotations

import json
from dataclasses import dataclass
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
