from __future__ import annotations

import sys
import unittest
from pathlib import Path
import shutil
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - depends on local test environment.
    TestClient = None

from agentic_knowledge_platform.container import build_container
from agentic_knowledge_platform.core.config import Settings
from agentic_knowledge_platform.main import create_app


@unittest.skipIf(TestClient is None, "FastAPI test client is not available")
class FrontendStaticTests(unittest.TestCase):
    def test_root_serves_built_frontend_when_dist_exists(self) -> None:
        dist_dir = ROOT / "test_artifacts" / f"frontend_static_case_{uuid4().hex}"
        assets_dir = dist_dir / "assets"
        assets_dir.mkdir(parents=True)
        (dist_dir / "index.html").write_text(
            "<!doctype html><html><body>cloudbase frontend shell</body></html>",
            encoding="utf-8",
        )
        (assets_dir / "app.js").write_text("console.log('ok');", encoding="utf-8")

        try:
            settings = Settings(frontend_dist_dir=str(dist_dir))
            app = create_app(build_container(settings))
            client = TestClient(app)

            root_response = client.get("/")
            asset_response = client.get("/assets/app.js")
        finally:
            shutil.rmtree(dist_dir, ignore_errors=True)

        self.assertEqual(root_response.status_code, 200)
        self.assertIn("cloudbase frontend shell", root_response.text)
        self.assertEqual(asset_response.status_code, 200)
        self.assertIn("console.log('ok');", asset_response.text)


if __name__ == "__main__":
    unittest.main()
