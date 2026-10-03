"""Node 2 - Planner: grade-weighted backward scheduling; on re-plan, shifts only flagged blocks."""
from datetime import datetime, timedelta
from typing import List

from pydantic import BaseModel

from src import llm
from src.tools.interval_engine import FMT, parse

BASE_DAYS = 2        # dT_prep = BASE_DAYS * (weight / 10)
START_HOUR = 18      # default study start time (6 PM)
BLOCK_HOURS = 2.0
DEFAULT_TITLES = ["Concept review", "Practice and drafting", "Final revision"]


class PhaseTitles(BaseModel):
    titles: List[str]


def phases_for(weight: float) -> int:
    return 3 if weight >= 25 else 2 if weight >= 10 else 1


def prep_days(weight: float) -> int:
    return max(1, min(21, round(BASE_DAYS * weight / 10)))


def get_titles(item: dict, n: int):
    """LLM names each study phase; falls back to defaults if the LLM is unavailable."""
    try:
        model = llm.structured(llm.get_llm(0.2), PhaseTitles)
        res = model.invoke(
            f"Give exactly {n} short study-phase titles (max 4 words each, in order) to prepare for "
            f"the {item['task_type']} '{item['task_name']}' in {item['course_name']}.")
        titles = [t.strip() for t in res.titles if t.strip()]
        if len(titles) >= n:
            return titles[:n]
    except Exception:
        pass
    return (["Quick review"] if n == 1 else DEFAULT_TITLES[:n]) if n < 3 else DEFAULT_TITLES


def build_milestones(items):
    out = []
    for it in sorted(items, key=lambda x: x["due_date"]):
        due = datetime.strptime(it["due_date"], "%Y-%m-%d")
        w, n = it["grade_weight_percent"], phases_for(it["grade_weight_percent"])
        pd_ = prep_days(w)
        offsets = sorted({max(1, round(pd_ * (n - k) / n)) for k in range(n)}, reverse=True)
        titles = get_titles(it, len(offsets))
        for k, off in enumerate(offsets):
            start = (due - timedelta(days=off)).replace(hour=START_HOUR)
            out.append({"course": it["course_name"], "task": it["task_name"],
                        "title": f"{it['task_name']}: {titles[k]}",
                        "start": start.strftime(FMT), "hours": BLOCK_HOURS})
    return out


def planner_node(state):
    if state.get("needs_replan") and state.get("proposed_milestones"):
        ms = [dict(m) for m in state["proposed_milestones"]]
        for idx in {c["index"] for c in state.get("conflict_details", [])}:
            ms[idx]["start"] = (parse(ms[idx]["start"]) - timedelta(days=1)).strftime(FMT)   # move 24 h earlier
        return {"proposed_milestones": ms, "needs_replan": False}
    return {"proposed_milestones": build_milestones(state["parsed_syllabus"]["items"]), "needs_replan": False}
