from typing import Any, Dict, List, TypedDict


class AcademicState(TypedDict, total=False):
    syllabus_text: str
    semester_start: str                 # YYYY-MM-DD, used for 'Week N' dates
    parsed_syllabus: Dict[str, Any]     # SyllabusData as dict
    proposed_milestones: List[dict]
    free_busy_slots: List[dict]
    conflict_details: List[dict]        # structured output of the interval engine
    conflicts_detected: List[str]       # critic feedback message(s)
    audit_iteration_count: int          # number of re-plans done (cap = 3)
    needs_replan: bool
    user_approved: bool
    dispatch_status: str
    ics_path: str
