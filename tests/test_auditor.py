from src.tools.interval_engine import find_conflicts


def ms(start, hours=2.0, title="Study"):
    return {"course": "CS101", "title": title, "start": start, "hours": hours}


def test_clean_schedule_has_no_conflicts():
    assert find_conflicts([ms("2026-10-10 18:00")], []) == []


def test_busy_overlap_detected():
    busy = [{"start": "2026-10-10 17:00", "end": "2026-10-10 21:00"}]   # 4-hour event
    c = find_conflicts([ms("2026-10-10 18:00")], busy)
    assert c and c[0]["type"] == "busy_overlap"


def test_touching_intervals_do_not_overlap():
    busy = [{"start": "2026-10-10 16:00", "end": "2026-10-10 18:00"}]
    assert find_conflicts([ms("2026-10-10 18:00")], busy) == []


def test_daily_cap_enforced():
    c = find_conflicts([ms("2026-10-10 09:00", title="A"), ms("2026-10-10 12:00", title="B")], [])
    assert [x["type"] for x in c] == ["daily_cap"] and c[0]["index"] == 1   # 4 h > 3 h cap


def test_study_blocks_overlapping_each_other():
    c = find_conflicts([ms("2026-10-10 18:00", title="A"), ms("2026-10-10 19:00", title="B")], [])
    assert any(x["type"] == "study_overlap" for x in c)
