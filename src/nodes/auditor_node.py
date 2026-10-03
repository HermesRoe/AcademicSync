"""Node 3 - Hybrid Auditor: deterministic Python check + Critic LLM message. Loop cap = 3."""
from datetime import timedelta

from src import llm
from src.tools import gcal_tool
from src.tools.interval_engine import find_conflicts, parse, span

MAX_REPLANS = 3
DAILY_CAP_HOURS = 3.0


def critic_feedback(conflicts) -> str:
    plain = " ".join(c["detail"] for c in conflicts)
    try:
        reply = llm.get_llm(0.2).invoke(
            "You are a scheduling critic. In at most two sentences, tell the planner what is wrong "
            "with this study schedule and to move the flagged blocks earlier. Conflicts: " + plain)
        return reply.content.strip()
    except Exception:
        return plain


def auditor_node(state):
    ms = state["proposed_milestones"]
    busy = state.get("free_busy_slots")
    if busy is None:                                   # fetch once, reuse on later iterations
        starts = [span(m)[0] for m in ms]
        ends = [span(m)[1] for m in ms]
        busy = gcal_tool.get_busy(min(starts) - timedelta(days=1), max(ends) + timedelta(days=1))
    conflicts = find_conflicts(ms, busy, DAILY_CAP_HOURS)
    count = state.get("audit_iteration_count", 0)
    if conflicts and count < MAX_REPLANS:
        return {"free_busy_slots": busy, "conflict_details": conflicts,
                "conflicts_detected": [critic_feedback(conflicts)],
                "audit_iteration_count": count + 1, "needs_replan": True}
    return {"free_busy_slots": busy, "conflict_details": conflicts,
            "conflicts_detected": [c["detail"] for c in conflicts], "needs_replan": False}
