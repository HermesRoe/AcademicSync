from datetime import datetime
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event

from src.tools.interval_engine import span

TZ = ZoneInfo("Asia/Kolkata")


def export_ics(milestones, path):
    cal = Calendar()
    cal.add("prodid", "-//AcademicSync//EN")
    cal.add("version", "2.0")
    for m in milestones:
        s, e = span(m)
        ev = Event()
        ev.add("uid", f"{m['event_id']}@academicsync")
        ev.add("summary", f"[Study] {m['title']}")
        ev.add("description", f"Course: {m['course']}")
        ev.add("dtstart", s.replace(tzinfo=TZ))
        ev.add("dtend", e.replace(tzinfo=TZ))
        ev.add("dtstamp", datetime.now(TZ))
        cal.add_component(ev)
    with open(path, "wb") as f:
        f.write(cal.to_ical())
    return str(path)
