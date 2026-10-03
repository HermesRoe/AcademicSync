from src.nodes import dispatcher_node as d
from src.tools import gcal_tool


def state():
    return {"user_approved": True, "proposed_milestones": [
        {"course": "CS101", "title": "Midterm: Review", "start": "2026-10-12 18:00", "hours": 2.0}]}


def test_second_run_creates_no_duplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(gcal_tool, "LEDGER", tmp_path / "ledger.json")
    monkeypatch.setattr(d, "ICS_PATH", tmp_path / "out.ics")
    monkeypatch.setenv("USE_GCAL", "false")
    first = d.dispatcher_node(state())["dispatch_status"]
    second = d.dispatcher_node(state())["dispatch_status"]
    assert first.startswith("1 event(s) created, 0")
    assert second.startswith("0 event(s) created, 1 duplicate")
    assert (tmp_path / "out.ics").read_bytes().startswith(b"BEGIN:VCALENDAR")


def test_blocked_without_approval():
    s = state(); s["user_approved"] = False
    assert "blocked" in d.dispatcher_node(s)["dispatch_status"]


def test_event_id_is_stable_md5():
    assert d.event_id("A", "B", "C") == d.event_id("A", "B", "C") and len(d.event_id("A", "B", "C")) == 32
