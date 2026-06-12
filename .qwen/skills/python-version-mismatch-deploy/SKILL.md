---
name: python-version-mismatch-deploy
description: Diagnose and fix Python version/library compatibility crashes in deployment when the runtime Python version differs from what was specified in Dockerfile or configs.
source: auto-skill
extracted_at: '2026-06-11T18:21:44.270Z'
---

# Diagnosing Python Version Mismatch in Deployments

Use this when a production deployment crashes with a TypeError or other runtime error, and the traceback reveals a different Python version than what your Dockerfile or configuration specifies.

## Step 1: Identify the mismatch

Look at the **file paths** in the traceback, not just the error message. The site-packages path reveals the actual Python version:

```
/opt/render/project/src/.venv/lib/python3.14/site-packages/...
```

Compare this against:
- The `FROM python:X.Y-slim` line in your Dockerfile
- Any `runtime.txt` or build configuration
- The Python version in your local dev environment

If they differ, the deployment platform is NOT using your Docker build — it's running a native Python environment.

## Step 2: Understand why Docker isn't being used

Common reasons:
- Docker build failed silently and the platform fell back to native Python
- Platform free tier doesn't properly honor `env: docker` in render.yaml
- Service was initially created as native Python and the render.yaml change didn't update it (you may need to delete and re-create the service)

## Step 3: Diagnose the specific compatibility issue

Python version changes often break libraries. Key patterns:

- **`Union.__getitem__` changes (Python 3.14)**: `typing.Union` subscripting behavior changed. Libraries that reconstruct Union types from stringified annotations (via `cast(Any, Union).__getitem__(types)`) will crash with: `TypeError: descriptor '__getitem__' requires a 'typing.Union' object but received a 'tuple'`
- **`from __future__ import annotations` amplifies the problem**: This makes all annotations strings, forcing libraries like SQLAlchemy to de-stringify them at runtime. The de-stringification step is where Python version incompatibilities surface.

## Step 4: Apply a multi-layered fix

Don't rely on a single fix. Apply all three layers so the app works regardless of which Python version the platform uses:

### Layer 1 — Upgrade the incompatible library
```
sqlalchemy==2.0.36 → sqlalchemy==2.0.50
```
Newer versions include compatibility fixes for newer Python versions. Check PyPI for the latest release.

### Layer 2 — Remove `from __future__ import annotations` from ORM/model files
This avoids the de-stringification code path entirely. Only remove it from files that define mapped SQLAlchemy models (files with `Mapped[]` annotations). Other files can keep it safely since they don't trigger annotation de-stringification.

Before removing, verify all annotation types are importable at class definition time (no forward references needed). If there ARE forward references, keep `from __future__ import annotations` and rely solely on Layer 1.

### Layer 3 — Add `runtime.txt` as a fallback pin
Create a `runtime.txt` file in the backend directory with the desired Python version (e.g., `3.11.9`). This tells Render and similar platforms which Python to use for native builds, providing a safety net if Docker isn't used.

## Step 5: Verify locally

1. Install the upgraded library: `pip install sqlalchemy==2.0.50`
2. Import the models: `python -c "from models.orm import PipelineORM, MemoryORM; print('OK')"`
3. If successful, the fix works for both the Docker Python version and the newer platform Python version.

## Why multiple layers matter

- **Layer 1 alone** might not fix all edge cases (the de-stringification path could still have issues)
- **Layer 2 alone** only works if the library handles annotations natively on the new Python version
- **Layer 3 alone** only works if the platform honors runtime.txt (some don't)
- **All three together** cover every scenario: upgraded library handles new Python, removed future import avoids the crash path, runtime.txt pins the version if Docker isn't used