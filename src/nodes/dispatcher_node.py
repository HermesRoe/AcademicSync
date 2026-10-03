"""Node 4 - Dispatcher: idempotent MD5 event IDs, Google Calendar (or mock) + .ics export."""
import hashlib
from pathlib import Path

from src.tools import gcal_tool
from src.tools.ics_exporter import export_ics

ICS_PATH = Path(__file__).resolve().parents[2] / "data" / "academic_schedule.ics"


def event_id(course: str, title: str, start: str) -> str:
    # MD5 hex uses only 0-9a-f, which is valid for Google Calendar event IDs.
    return hashlib.md5(f"{course}{title}{start}".encode("utf-8")).hexdigest()


def dispatcher_node(state):
    if not state.get("user_approved"):
        return {"dispatch_status": "blocked: user approval required"}
    ms = [dict(m) for m in state["proposed_milestones"]]
    for m in ms:
        m["event_id"] = event_id(m["course"], m["title"], m["start"])
    created = skipped = 0
    if gcal_tool.is_live():
        svc = gcal_tool._service()
        for m in ms:
            if gcal_tool.event_exists(svc, m["event_id"]):
                skipped += 1
            else:
                gcal_tool.insert_event(svc, m)
                created += 1
        mode = "Google Calendar"
    else:
        ledger = gcal_tool.load_ledger()
        for m in ms:
            if m["event_id"] in ledger:
                skipped += 1
            else:
                ledger.add(m["event_id"])
                created += 1
        gcal_tool.save_ledger(ledger)
        mode = "mock calendar"
    export_ics(ms, ICS_PATH)
    return {"proposed_milestones": ms, "ics_path": str(ICS_PATH),
            "dispatch_status": f"{created} event(s) created, {skipped} duplicate(s) skipped ({mode}); .ics file written."}
