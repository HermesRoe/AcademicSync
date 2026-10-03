from src.graph import build_graph
from src.nodes import parser_node
from src.schemas import DeliverableItem, SyllabusData


def fake_syllabus():
    return SyllabusData(items=[DeliverableItem(
        course_name="CS101", task_name="Midterm", due_date="2026-10-15",
        grade_weight_percent=25, task_type="exam")])


def run(monkeypatch, busy):
    monkeypatch.setattr(parser_node, "llm_extract", lambda c, s: fake_syllabus())
    return build_graph().invoke({"syllabus_text": "x" * 20, "semester_start": "2026-08-10",
                                 "free_busy_slots": busy, "audit_iteration_count": 0, "user_approved": False})


def test_conflict_resolved_by_replanning(monkeypatch):
    busy = [{"start": "2026-10-10 17:00", "end": "2026-10-10 21:00"}]
    out = run(monkeypatch, busy)
    assert out["audit_iteration_count"] == 1 and out["conflict_details"] == []


def test_two_loops(monkeypatch):
    busy = [{"start": "2026-10-10 17:00", "end": "2026-10-10 21:00"},
            {"start": "2026-10-09 17:00", "end": "2026-10-09 21:00"}]
    out = run(monkeypatch, busy)
    assert out["audit_iteration_count"] == 2 and out["conflict_details"] == []


def test_loop_is_capped_at_three(monkeypatch):
    busy = [{"start": f"2026-10-{d:02d} 00:00", "end": f"2026-10-{d:02d} 23:59"} for d in range(1, 16)]
    out = run(monkeypatch, busy)
    assert out["audit_iteration_count"] == 3          # never more than 3
    assert out["conflict_details"]                    # escalated to the user with conflicts listed
    assert out["dispatch_status"] == "awaiting user approval"
