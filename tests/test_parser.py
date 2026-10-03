import pytest
from pydantic import ValidationError

from src.nodes import parser_node
from src.schemas import DeliverableItem, SyllabusData


def item(**kw):
    base = dict(course_name="CS101", task_name="Midterm", due_date="2026-10-15",
                grade_weight_percent=25, task_type="exam")
    base.update(kw)
    return DeliverableItem(**base)


def test_valid_item():
    assert item().grade_weight_percent == 25


def test_bad_date_rejected():
    with pytest.raises(ValidationError):
        item(due_date="15/10/2026")


def test_weight_over_100_rejected():
    with pytest.raises(ValidationError):
        item(grade_weight_percent=150)


def test_relative_week_resolved():
    it = item(task_name="Quiz 1", due_date=None, relative_week=11, task_type="quiz")
    out = parser_node.resolve_dates([it], "2026-08-10")
    assert out[0].due_date == "2026-10-23"


def test_relative_week_needs_start_date():
    it = item(due_date=None, relative_week=3)
    with pytest.raises(ValueError):
        parser_node.resolve_dates([it], None)


def test_node_with_fake_llm(monkeypatch):
    fake = SyllabusData(items=[item(), item(task_name="Midterm (dup)")])
    monkeypatch.setattr(parser_node, "llm_extract", lambda chunk, start: fake)
    out = parser_node.parser_node({"syllabus_text": "x" * 50, "semester_start": "2026-08-10"})
    assert len(out["parsed_syllabus"]["items"]) == 1   # duplicate removed
