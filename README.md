# VoteAssist AI

VoteAssist AI is a complete local academic demonstration of an election-operations assistant. It uses **synthetic/fictitious data only**. It is not connected to government systems, does not represent real voters, and does not make legal eligibility or election outcome decisions.

## Included

- Deterministic generator for exactly 25,000 synthetic voter records and 50 stations (`SEED = 42`)
- FastAPI backend with verified dashboard, voter search/detail, station analytics, anomaly queue, audit log, chat tool routing, RAG procedure responses, and report generation
- Responsive frontend operations console with charts, tables, anomaly explanations, and an AI assistant
- Local knowledge-base documents for grounded procedural answers

## Run locally

```powershell
cd c:\Users\Jessikala\Downloads\VoterApp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\generate_dataset.py
uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000`.

Demo login credentials are `Alcina`, `Akshaya`, or `Ajay` / `demo123`.

## API smoke checks

- `GET /api/health`
- `GET /api/dashboard/summary`
- `GET /api/voters?search=VOTER001000`
- `GET /api/anomalies`
- `POST /api/chat` with `{ "message": "How is PS-014 performing?" }`
- `POST /api/reports/generate`

## Architecture notes

The local tool router is deliberately provider-neutral. It behaves as a safe fallback when no LLM key is configured and only exposes read-only, structured backend tools to the browser. An external LLM provider can be added behind the `/api/chat` boundary later without changing the UI. The dataset module is the source of truth for all numbers shown in the app.
