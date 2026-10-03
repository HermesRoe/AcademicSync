"""Node 1 - Parser: chunk syllabus text, extract deliverables with a Pydantic schema."""
from collections import Counter
from datetime import datetime, timedelta

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src import llm
from src.schemas import SyllabusData

PROMPT = """You extract graded deliverables from a university course syllabus.
Return every exam, quiz, project and assignment that has a grade weight.
Rules:
- grade_weight_percent is a number between 0 and 100.
- If a full date is given, put it in due_date as YYYY-MM-DD. If the year is missing, use the year of the semester start ({start}).
- If only a relative label such as 'Week 5' is given, set relative_week to that number and leave due_date null.
- course_name is the course code and title from the syllabus header; if it is not in this text use 'UNKNOWN'.
- task_type is one of: exam, project, quiz, assignment.
- Do not invent items. If the text has no graded deliverables return an empty list.

SYLLABUS TEXT:
{chunk}"""


def llm_extract(chunk: str, semester_start: str) -> SyllabusData:
    model = llm.structured(llm.get_llm(0), SyllabusData)
    last = None
    for _ in range(2):                                # small local models sometimes need a second try
        try:
            return model.invoke(PROMPT.format(start=semester_start, chunk=chunk))
        except Exception as e:
            last = e
    raise last


def resolve_dates(items, semester_start):
    """Turn 'Week N' into a real date (Friday of that week). Deterministic, no LLM."""
    out = []
    for it in items:
        if it.due_date is None:
            if it.relative_week is None:
                continue                      # no usable date -> dropped
            if not semester_start:
                raise ValueError("Semester start date is required for 'Week N' deadlines.")
            d = datetime.strptime(semester_start, "%Y-%m-%d") + timedelta(days=(it.relative_week - 1) * 7 + 4)
            it = it.model_copy(update={"due_date": d.strftime("%Y-%m-%d")})
        out.append(it)
    return out


def merge_items(items):
    """Remove duplicates created by overlapping chunks; fix UNKNOWN course names."""
    seen, merged = set(), []
    for it in items:
        key = (it.due_date, it.grade_weight_percent, it.task_type)
        if key not in seen:
            seen.add(key)
            merged.append(it)
    names = [i.course_name for i in merged if i.course_name.upper() != "UNKNOWN"]
    main = Counter(names).most_common(1)[0][0] if names else "Course"
    return [i.model_copy(update={"course_name": main}) if i.course_name.upper() == "UNKNOWN" else i for i in merged]


def parser_node(state):
    start = state.get("semester_start")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    items = []
    for chunk in splitter.split_text(state["syllabus_text"]):
        items.extend(llm_extract(chunk, start).items)
    items = merge_items(resolve_dates(items, start))
    return {"parsed_syllabus": {"items": [i.model_dump() for i in items]}, "audit_iteration_count": 0}
