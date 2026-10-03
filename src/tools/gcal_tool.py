"""Google Calendar access. MOCK mode (default) reads data/busy_mock.json and keeps a local ledger."""
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.tools.interval_engine import FMT, span

TZ = "Asia/Kolkata"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
ROOT = Path(__file__).resolve().parents[2]
MOCK_BUSY = ROOT / "data" / "busy_mock.json"
LEDGER = ROOT / "data" / "dispatched_ids.json"


def is_live() -> bool:
    return os.getenv("USE_GCAL", "false").lower() == "true"


def _service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    token, creds = ROOT / "token.json", None
    if token.exists():
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())          # automatic token refresh
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(ROOT / "credentials.json"), SCOPES)
            creds = flow.run_local_server(port=0)
        token.write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def get_busy(start: datetime, end: datetime):
    """Busy intervals as [{'start','end'}] in local (Asia/Kolkata) time."""
    if not is_live():
        return json.loads(MOCK_BUSY.read_text()) if MOCK_BUSY.exists() else []
    tz = ZoneInfo(TZ)
    res = _service().events().list(
        calendarId="primary", timeMin=start.replace(tzinfo=tz).isoformat(),
        timeMax=end.replace(tzinfo=tz).isoformat(), singleEvents=True, orderBy="startTime").execute()
    out = []
    for ev in res.get("items", []):
        if ev.get("extendedProperties", {}).get("private", {}).get("source") == "academicsync":
            continue                          # ignore our own events so re-runs stay idempotent
        if ev.get("transparency") == "transparent" or "dateTime" not in ev.get("start", {}):
            continue                          # skip 'free' and all-day events
        s = datetime.fromisoformat(ev["start"]["dateTime"].replace("Z", "+00:00")).astimezone(tz)
        e = datetime.fromisoformat(ev["end"]["dateTime"].replace("Z", "+00:00")).astimezone(tz)
        out.append({"start": s.replace(tzinfo=None).strftime(FMT), "end": e.replace(tzinfo=None).strftime(FMT)})
    return out


def event_exists(service, event_id: str) -> bool:
    from googleapiclient.errors import HttpError
    try:
        service.events().get(calendarId="primary", eventId=event_id).execute()
        return True
    except HttpError as e:
        if e.resp.status == 404:
            return False
        raise


def insert_event(service, m: dict):
    s, e = span(m)
    body = {
        "id": m["event_id"],
        "summary": f"[Study] {m['title']}",
        "description": f"Course: {m['course']} (created by AcademicSync)",
        "start": {"dateTime": s.isoformat(), "timeZone": TZ},
        "end": {"dateTime": e.isoformat(), "timeZone": TZ},
        "extendedProperties": {"private": {"source": "academicsync"}},
    }
    service.events().insert(calendarId="primary", body=body).execute()


def load_ledger() -> set:
    return set(json.loads(LEDGER.read_text())) if LEDGER.exists() else set()


def save_ledger(ids: set):
    LEDGER.write_text(json.dumps(sorted(ids)))
