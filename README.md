# BrandLens

BrandLens is an evidence-first, human-led brand governance demo. Submit marketing copy, check it against a shared brand policy, inspect exact quotes and their rule/fact-register citations, then record a human approval or request for changes.

## What works

- Deterministic checks for configurable banned phrases and numeric/absolute claims.
- Explainable findings with the exact quoted draft text, policy source ID, severity, reason, and next step.
- A brand-policy page for adding banned phrases and approved facts.
- A human approval / request-changes decision with optional reviewer notes and an audit trail.
- A saved review history backed by SQLite.
- A seeded sample draft for a judge to try immediately.

Checks are deterministic heuristics, not an LLM, legal review, or a guarantee that copy is compliant. Unsupported-claim matching is exact and intentionally favors human verification over inferred evidence. This build reviews pasted text; file and image review are not included.

## Round 2 submission PDF

`BrandLens_Round2_Submission.pdf` records the completed features, technology, plan changes, test evidence, and three planned Round 3 improvements. To regenerate it after replacing the pending public links with the final app and repository URLs:

```powershell
.\.venv\Scripts\python.exe -m pip install -r docs-requirements.txt
.\.venv\Scripts\python.exe build_submission_pdf.py
```

Do not submit the PDF until its public app and source-repository links have been updated.

## Run locally

Prerequisites: Python 3.10+ and Node.js 20.19+ (or 22.12+).

From the project root, start the API in one terminal:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

In a second terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open the Vite URL (normally `http://localhost:5173`). The frontend proxies API requests to `http://127.0.0.1:8000`. API health is available at `http://localhost:8000/health`.

SQLite is created at `backend\brandlens.db` by default. Set `BRANDLENS_DB_PATH` to use a different location or a persistent deployment disk. Do not submit confidential or personal content to this public demo.

## Verify

```powershell
.\.venv\Scripts\python.exe -m unittest backend.test_brandlens
Set-Location frontend
npm run lint
npm run build
```

## Deploy a single public demo

This repository includes a multi-stage `Dockerfile` and a Render Blueprint (`render.yaml`) for one public web service. From Render, select **New > Blueprint**, connect this public repository, and deploy. The container builds the React frontend and serves it and the FastAPI API from the same origin. Check `/health` after deployment.

The free-demo configuration writes SQLite data to `/tmp`, which is temporary: reviews and policy changes can disappear when the service restarts or redeploys, and the free service may take time to wake up. Use a persistent disk and set `BRANDLENS_DB_PATH` to its mount path if review history must survive. Do not submit confidential or personal content to the unauthenticated public demo. The public demo has no login, role-based access, backups, or security boundary between visitors.

For local deployment testing, build and run the Docker image from the repository root:

```powershell
docker build -t brandlens .
docker run --rm -p 8000:8000 -e BRANDLENS_DB_PATH=/tmp/brandlens.db brandlens
```

The public project and repository URLs must be added to the submission PDF after deployment and public repository creation. No public URL is claimed until those steps are complete.

## Round 1 plan changes

- Kept the planned FastAPI/React stack and SQLite demo datastore.
- Delivered paste-in text review, a starter policy, configurable banned terms/facts, human decisions, and audit/history first.
- Deferred document uploads, image checks, role-based access, external AI/retrieval, tracked edits, and analytics rather than claiming incomplete features.
- Round 3 additions remain image review, guideline-health insights, and verifier reliability tuning against a seeded test set.
