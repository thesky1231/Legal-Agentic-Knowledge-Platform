# Releases and Deployment

## First principle

GitHub Releases and project deployment are related, but they are not the same thing.

- A **Release** is a versioned package page for tagged source bundles and notes.
- A **Deployment** is how someone actually runs the project locally or in a container.

For this repository:

- Releases are used to publish tagged source snapshots.
- `docker compose up --build` is the fastest reproducible local deployment path.

## Fastest way to run the project

### Option 1: local Python environment

If you already have a Python 3.12 environment with `fastapi` and `uvicorn`:

```bash
python scripts/demo_showcase.py
python scripts/run_eval.py
python -m uvicorn --app-dir src agentic_knowledge_platform.main:create_app --factory
```

### Option 2: Docker Compose

This is the closest thing to a one-command deployment for outside users:

```bash
cp .env.example .env
docker compose up --build
```

After startup, open:

- `http://localhost:8000/health`
- `http://localhost:8000/ops/overview`
- `http://localhost:8000/metrics`

## Legal demo assets included in the release

The public source tree includes a legal-domain demo input:

- `examples/legal/legal_assistant_handbook.md`

This keeps the runnable demo aligned with the legal RAG / legal agent story described in the repository.

## How GitHub Releases are produced

The repository includes a GitHub Actions workflow that creates a GitHub Release whenever a tag like `v0.1.1` is pushed.

The workflow publishes:

- a `.tar.gz` source bundle
- a `.zip` source bundle
- auto-generated release notes

## Recommended release flow

1. Update `CHANGELOG.md`
2. Commit and push `main`
3. Create a tag
4. Push the tag

Example:

```bash
git tag -a v0.1.1 -m "v0.1.1 legal demo alignment and release workflow"
git push origin v0.1.1
```

Once the tag reaches GitHub, the release workflow should create the Release page automatically.

## What to tell outside users

If someone asks “how do I try this project quickly?”, the best answer is:

1. Download the latest GitHub Release source archive or clone the repository
2. Copy `.env.example` to `.env`
3. Run `docker compose up --build`

That is the cleanest external trial path for this project today.
