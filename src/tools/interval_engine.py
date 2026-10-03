"""Deterministic interval maths. No LLM is used here on purpose."""
from collections import defaultdict
from datetime import datetime, timedelta

FMT = "%Y-%m-%d %H:%M"


def parse(s: str) -> datetime:
    return datetime.strptime(s, FMT)


def span(m: dict):
    s = parse(m["start"])
    return s, s + timedelta(hours=float(m["hours"]))


def overlaps(a_s, a_e, b_s, b_e) -> bool:
    return a_s < b_e and b_s < a_e


def find_conflicts(milestones, busy, daily_cap: float = 3.0):
    """Return a list of {index, type, detail}. Types: busy_overlap, study_overlap, daily_cap."""
    busy_iv = [(parse(b["start"]), parse(b["end"])) for b in busy]
    spans = [span(m) for m in milestones]
    out, seen = [], set()

    def add(i, kind, detail):
        if (i, kind) not in seen:
            seen.add((i, kind))
            out.append({"index": i, "type": kind, "detail": detail})

    for i, (s, e) in enumerate(spans):
        title = milestones[i]["title"]
        for bs, be in busy_iv:
            if overlaps(s, e, bs, be):
                add(i, "busy_overlap", f"'{title}' ({s:%d %b %H:%M}-{e:%H:%M}) clashes with a calendar event ({bs:%H:%M}-{be:%H:%M}).")
        for j in range(i + 1, len(spans)):
            if overlaps(s, e, *spans[j]):
                add(j, "study_overlap", f"'{milestones[j]['title']}' overlaps another study block on {s:%d %b}.")

    by_day = defaultdict(list)
    for i, (s, _) in enumerate(spans):
        by_day[s.date()].append(i)
    for day, idxs in by_day.items():
        total = 0.0
        for i in sorted(idxs, key=lambda k: spans[k][0]):
            total += float(milestones[i]["hours"])
            if total > daily_cap + 1e-9:
                add(i, "daily_cap", f"{day:%d %b}: study load {total:g} h exceeds the {daily_cap:g} h daily cap.")
    return out
