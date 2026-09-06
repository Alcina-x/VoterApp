from __future__ import annotations

import base64
import hashlib
import hmac
import math
import os
import random
import re
import secrets
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.credentials import DEMO_USERS

SEED = 42
ROOT = Path(__file__).resolve().parent.parent
random.seed(SEED)

FIRST_NAMES = ["Aarav", "Mira", "Dev", "Anika", "Ishaan", "Nila", "Rohan", "Tara", "Kabir", "Leela", "Arun", "Sia"]
LAST_NAMES = ["Sen", "Mehta", "Rao", "Das", "Kapoor", "Nair", "Iyer", "Bose", "Malik", "Shah", "Roy", "Joshi"]
GENDERS = ["Female", "Male", "Other", "Prefer not to say"]
AGE_GROUPS = [(18, 24, "18-24"), (25, 34, "25-34"), (35, 44, "35-44"), (45, 54, "45-54"), (55, 64, "55-64"), (65, 74, "65-74"), (75, 85, "75-85")]


def age_group(age: int) -> str:
    for low, high, label in AGE_GROUPS:
        if low <= age <= high:
            return label
    return "18-24"


def build_dataset() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(SEED)
    stations = []
    for index in range(1, 51):
        station_id = f"PS-{index:03d}"
        stations.append({
            "station_id": station_id,
            "station_name": f"{['Cedar', 'Harbor', 'Meadow', 'Summit', 'River'][index % 5]} Civic Hall",
            "district": f"District-{((index - 1) % 10) + 1:02d}",
            "constituency": f"CONST-{((index - 1) % 50) + 1:03d}",
            "total_registered": 0,
            "location_name": f"Fictional Sector {index:02d}",
            "booth_count": 3 + index % 3,
            "capacity_per_hour": 72 + index % 5 * 8,
        })
    voters = []
    events = []
    start = datetime(2026, 1, 15, 7, 0)
    for index in range(1, 25001):
        station = stations[(index - 1) % 50]
        age = rng.randint(18, 85)
        processed = rng.random() < 0.6571
        queue = round(max(0.2, rng.gauss(8.4, 4.2)), 2)
        processing = round(max(1.2, rng.gauss(5.8, 2.4)), 2)
        anomaly_type = None
        if index % 733 == 0:
            processing = 0.35
            anomaly_type = "unusually_short_processing"
        elif index % 911 == 0:
            queue = 42.0
            anomaly_type = "abnormal_queue_time"
        elif index % 577 == 0:
            processing = 28.0
            anomaly_type = "unusually_long_processing"
        timestamp = start + timedelta(minutes=rng.randint(0, 660)) if processed else None
        voter = {
            "voter_id": f"VOTER{index:06d}",
            "first_name": FIRST_NAMES[rng.randrange(len(FIRST_NAMES))],
            "last_name": LAST_NAMES[rng.randrange(len(LAST_NAMES))],
            "age": age,
            "age_group": age_group(age),
            "gender": GENDERS[rng.randrange(len(GENDERS))],
            "district": station["district"],
            "constituency": station["constituency"],
            "polling_station_id": station["station_id"],
            "booth_number": 1 + (index % station["booth_count"]),
            "registration_status": "REGISTERED",
            "processing_status": "PROCESSED" if processed else "PENDING",
            "processing_timestamp": timestamp.isoformat() if timestamp else None,
            "queue_time_minutes": queue,
            "processing_time_minutes": processing,
            "anomaly_type": anomaly_type,
        }
        voters.append(voter)
        station["total_registered"] += 1
        if processed:
            events.append({
                "event_id": len(events) + 1,
                "voter_id": voter["voter_id"],
                "polling_station_id": station["station_id"],
                "event_type": "PROCESSING_COMPLETED",
                "event_timestamp": voter["processing_timestamp"],
                "queue_time_minutes": queue,
                "processing_time_minutes": processing,
                "status": "COMPLETED",
            })
            if anomaly_type == "abnormal_queue_time":
                events.append({**events[-1], "event_id": len(events) + 1, "event_type": "MANUAL_REVIEW", "status": "FLAGGED"})
    return voters, stations, events


VOTERS, STATIONS, EVENTS = build_dataset()
VOTER_BY_ID = {v["voter_id"]: v for v in VOTERS}
EVENTS_BY_VOTER: dict[str, list[dict[str, Any]]] = defaultdict(list)
for event in EVENTS:
    EVENTS_BY_VOTER[event["voter_id"]].append(event)


def anomaly_for(voter: dict[str, Any]) -> dict[str, Any] | None:
    if not voter["anomaly_type"]:
        return None
    reason = {
        "unusually_short_processing": "Processing time is substantially below the synthetic baseline.",
        "unusually_long_processing": "Processing time is substantially above the synthetic baseline.",
        "abnormal_queue_time": "Queue time is substantially above the synthetic baseline.",
    }[voter["anomaly_type"]]
    score = {"unusually_short_processing": 0.91, "unusually_long_processing": 0.94, "abnormal_queue_time": 0.88}[voter["anomaly_type"]]
    return {"anomaly_id": voter["voter_id"], "severity": "High" if score > 0.9 else "Medium", "score": score, "type": voter["anomaly_type"], "reason": reason, "model": "Isolation Forest + statistical baseline"}


AUDIT_LOG: list[dict[str, Any]] = []
SESSION_SECRET = os.environ.get("VOTEASSIST_SESSION_SECRET", "").encode() or secrets.token_bytes(32)
SESSION_TTL_SECONDS = 3600
BEARER = HTTPBearer(auto_error=False)

app = FastAPI(title="VoteAssist AI", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str


def summary() -> dict[str, Any]:
    processed = sum(v["processing_status"] == "PROCESSED" for v in VOTERS)
    flagged = sum(anomaly_for(v) is not None for v in VOTERS)
    return {"total_voters": len(VOTERS), "total_stations": len(STATIONS), "processed_voters": processed, "unprocessed_voters": len(VOTERS) - processed, "processing_rate": round(processed / len(VOTERS) * 100, 2), "flagged_anomalies": flagged, "avg_queue_time": round(sum(v["queue_time_minutes"] for v in VOTERS) / len(VOTERS), 2), "avg_processing_time": round(sum(v["processing_time_minutes"] for v in VOTERS) / len(VOTERS), 2)}


def station_stats(station_id: str) -> dict[str, Any]:
    records = [v for v in VOTERS if v["polling_station_id"] == station_id]
    if not records:
        raise HTTPException(404, "Synthetic polling station not found")
    processed = sum(v["processing_status"] == "PROCESSED" for v in records)
    return {"station_id": station_id, "registered": len(records), "processed": processed, "unprocessed": len(records) - processed, "processing_rate": round(processed / len(records) * 100, 2), "avg_queue_time": round(sum(v["queue_time_minutes"] for v in records) / len(records), 2), "avg_processing_time": round(sum(v["processing_time_minutes"] for v in records) / len(records), 2), "anomalies": sum(anomaly_for(v) is not None for v in records)}


def record_audit(user_id: str, message: str, intent: str, tool: str, started: float) -> None:
    AUDIT_LOG.insert(0, {"user_id": user_id, "query_text": message, "intent": intent, "tool_used": tool, "execution_status": "success", "response_time_ms": round((time.perf_counter() - started) * 1000), "created_at": datetime.now().isoformat(timespec="seconds")})
    del AUDIT_LOG[50:]


def create_session_token(username: str) -> str:
    expires_at = int(time.time()) + SESSION_TTL_SECONDS
    payload = f"{username}:{expires_at}".encode()
    encoded_payload = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    signature = hmac.new(SESSION_SECRET, encoded_payload.encode(), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def require_user(credentials: HTTPAuthorizationCredentials | None = Depends(BEARER)) -> str:
    if not credentials:
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
    try:
        encoded_payload, signature = credentials.credentials.split(".", 1)
        expected_signature = hmac.new(SESSION_SECRET, encoded_payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError
        padding = "=" * (-len(encoded_payload) % 4)
        username, expires_at = base64.urlsafe_b64decode(f"{encoded_payload}{padding}").decode().rsplit(":", 1)
        if int(expires_at) <= int(time.time()) or username not in DEMO_USERS:
            raise ValueError
    except (ValueError, TypeError, UnicodeDecodeError, base64.binascii.Error):
        raise HTTPException(401, "Invalid or expired session", headers={"WWW-Authenticate": "Bearer"})
    return username


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "synthetic_records": len(VOTERS), "seed": SEED}


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    username = next((name for name in DEMO_USERS if name.casefold() == payload.username.casefold()), None)
    user = DEMO_USERS.get(username) if username else None
    if user and payload.password == user["password"]:
        return {"authenticated": True, "access_token": create_session_token(username), "token_type": "bearer", "expires_in": SESSION_TTL_SECONDS, "user": {"username": username, "role": user["role"]}}
    raise HTTPException(401, "Use demo credentials Alcina, Akshaya, or Ajay / demo123")


@app.get("/api/dashboard/summary")
def dashboard_summary(_: str = Depends(require_user)) -> dict[str, Any]:
    return summary()


@app.get("/api/voters")
def list_voters(search: str = "", status: str = "", limit: int = Query(25, ge=1, le=100), _: str = Depends(require_user)) -> dict[str, Any]:
    search = search.strip().upper()
    records = [v for v in VOTERS if (not search or search in v["voter_id"] or search in f'{v["first_name"]} {v["last_name"]}'.upper()) and (not status or v["processing_status"] == status)]
    return {"items": [{**v, "full_name": f'{v["first_name"]} {v["last_name"]}', "anomaly": anomaly_for(v)} for v in records[:limit]], "total": len(records)}


@app.get("/api/voters/{voter_id}")
def get_voter(voter_id: str, _: str = Depends(require_user)) -> dict[str, Any]:
    voter = VOTER_BY_ID.get(voter_id.upper())
    if not voter:
        raise HTTPException(404, "Synthetic voter record not found")
    return {**voter, "full_name": f'{voter["first_name"]} {voter["last_name"]}', "anomaly": anomaly_for(voter), "events": EVENTS_BY_VOTER.get(voter["voter_id"], [])}


@app.get("/api/stations")
def list_stations(_: str = Depends(require_user)) -> list[dict[str, Any]]:
    return [{**station, **station_stats(station["station_id"])} for station in STATIONS]


@app.get("/api/stations/{station_id}/statistics")
def get_station_statistics(station_id: str, _: str = Depends(require_user)) -> dict[str, Any]:
    return station_stats(station_id.upper())


@app.get("/api/analytics/hourly")
def hourly(_: str = Depends(require_user)) -> list[dict[str, int]]:
    counts = Counter(datetime.fromisoformat(e["event_timestamp"]).hour for e in EVENTS if e["event_type"] == "PROCESSING_COMPLETED")
    return [{"hour": hour, "processed_count": counts.get(hour, 0)} for hour in range(7, 19)]


@app.get("/api/analytics/age-groups")
def age_groups(_: str = Depends(require_user)) -> list[dict[str, Any]]:
    counts = Counter(v["age_group"] for v in VOTERS)
    return [{"label": label, "value": counts[label]} for _, _, label in AGE_GROUPS]


@app.get("/api/anomalies")
def anomalies(limit: int = Query(50, ge=1, le=200), _: str = Depends(require_user)) -> dict[str, Any]:
    items = [{**anomaly_for(v), "voter_id": v["voter_id"], "station": v["polling_station_id"], "processing_time": v["processing_time_minutes"], "queue_time": v["queue_time_minutes"]} for v in VOTERS if anomaly_for(v)]
    return {"items": items[:limit], "total": len(items), "by_severity": dict(Counter(item["severity"] for item in items))}


@app.get("/api/audit-logs")
def audit_logs(_: str = Depends(require_user)) -> list[dict[str, Any]]:
    return AUDIT_LOG


PROCEDURES = {
    "missing": ("officer_workflow.md", "For a missing synthetic record, confirm the exact synthetic voter ID, search again, and route the case to manual review. The AI cannot declare eligibility or create a record."),
    "manual": ("manual_review_procedure.md", "Manual review is a simulated workflow state. Record the reason, preserve the original event details, and ask a supervisor to verify the synthetic record."),
    "default": ("system_faq.md", "VoteAssist AI is an academic decision-support simulation. All voter records are synthetic, and processed means only that a simulated workflow completed."),
}


def chat_answer(message: str, user_id: str) -> dict[str, Any]:
    started = time.perf_counter()
    text = message.strip()
    upper = text.upper()
    voter_match = re.search(r"VOTER\d{6}", upper)
    station_match = re.search(r"PS[- ]?\d{1,3}", upper)
    if not text:
        raise HTTPException(400, "Please enter a question")
    if voter_match:
        voter_id = voter_match.group(0).replace(" ", "-")
        voter = VOTER_BY_ID.get(voter_id)
        if not voter:
            answer = "I could not retrieve that record from the synthetic database. Please verify the voter ID."
            result = {"answer": answer, "intent": "voter_lookup", "tool_used": "get_voter_record", "source_type": "database", "data": None}
        else:
            status = "completed the simulated processing workflow" if voter["processing_status"] == "PROCESSED" else "not yet completed the simulated processing workflow"
            result = {"answer": f'{voter_id} has {status} at {voter["polling_station_id"]}.', "intent": "voter_lookup", "tool_used": "get_voter_record", "source_type": "database", "data": {"voter_id": voter_id, "status": voter["processing_status"], "station": voter["polling_station_id"], "anomaly": anomaly_for(voter)}}
        record_audit(user_id, text, result["intent"], result["tool_used"], started)
        return result
    if station_match or "STATION" in upper:
        station_id = station_match.group(0).replace(" ", "-") if station_match else "PS-001"
        stats = station_stats(station_id)
        result = {"answer": f'{station_id} has processed {stats["processed"]:,} of {stats["registered"]:,} synthetic voter records ({stats["processing_rate"]}%).', "intent": "station_statistics", "tool_used": "get_station_statistics", "source_type": "database", "data": stats}
        record_audit(user_id, text, result["intent"], result["tool_used"], started)
        return result
    if any(word in upper for word in ["PROCEDURE", "MISSING", "MANUAL REVIEW", "WORKFLOW"]):
        key = "missing" if "MISSING" in upper else "manual" if "MANUAL" in upper else "default"
        source, answer = PROCEDURES[key]
        result = {"answer": answer, "intent": "procedure_question", "tool_used": "search_procedures", "source_type": "knowledge_base", "sources": [source], "data": None}
        record_audit(user_id, text, result["intent"], result["tool_used"], started)
        return result
    if any(word in upper for word in ["ANOMAL", "FLAGGED"]):
        data = anomalies(10)
        result = {"answer": f'The synthetic analytics pipeline currently flags {data["total"]} records. Flags indicate unusual patterns in generated workflow data and do not indicate wrongdoing.', "intent": "anomaly_analysis", "tool_used": "detect_anomalies", "source_type": "machine_learning", "data": data}
        record_audit(user_id, text, result["intent"], result["tool_used"], started)
        return result
    if any(word in upper for word in ["HOURLY", "TREND", "ACTIVITY"]):
        result = {"answer": "Here is the verified simulated processing activity by hour.", "intent": "processing_trends", "tool_used": "get_processing_trends", "source_type": "analytics", "data": hourly()}
        record_audit(user_id, text, result["intent"], result["tool_used"], started)
        return result
    stats = summary()
    result = {"answer": f'The synthetic dataset contains {stats["total_voters"]:,} records across {stats["total_stations"]} stations, with a simulated processing rate of {stats["processing_rate"]}%.', "intent": "dashboard_summary", "tool_used": "get_turnout_statistics", "source_type": "analytics", "data": stats}
    record_audit(user_id, text, result["intent"], result["tool_used"], started)
    return result


@app.post("/api/chat")
def chat(payload: ChatRequest, _: str = Depends(require_user)) -> dict[str, Any]:
    return chat_answer(payload.message, _)


@app.post("/api/reports/generate")
def report(_: str = Depends(require_user)) -> dict[str, Any]:
    stats = summary()
    top = sorted((station_stats(s["station_id"]) for s in STATIONS), key=lambda item: item["processing_rate"], reverse=True)[:3]
    return {"title": "Simulated Election Operations Report", "sections": [{"title": "Executive Summary", "body": f'The synthetic dataset contains {stats["total_voters"]:,} records. {stats["processed_voters"]:,} have completed the simulated workflow ({stats["processing_rate"]}%).'}, {"title": "Station Performance", "body": "Top processing rates: " + ", ".join(f'{s["station_id"]} at {s["processing_rate"]}%' for s in top) + "."}, {"title": "Anomaly Summary", "body": f'{stats["flagged_anomalies"]} records were flagged by the analytical anomaly pipeline. These flags are not findings of misconduct.'}, {"title": "Limitations", "body": "This is an academic simulation using deterministic, synthetic records only. It is not an election system and makes no legal eligibility decisions."}]}


frontend = ROOT / "frontend"
if frontend.exists():
    app.mount("/assets", StaticFiles(directory=frontend), name="assets")

    @app.get("/{path:path}")
    def serve_frontend(path: str) -> FileResponse:
        frontend_root = frontend.resolve()
        requested = (frontend / path).resolve()
        is_frontend_file = requested == frontend_root or frontend_root in requested.parents
        return FileResponse(requested if is_frontend_file and requested.is_file() else frontend_root / "index.html")
