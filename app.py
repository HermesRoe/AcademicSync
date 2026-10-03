from datetime import date, datetime

import pandas as pd
import streamlit as st
from pypdf import PdfReader

from src.graph import build_graph
from src.tools import gcal_tool
from src.tools.interval_engine import FMT, find_conflicts

st.set_page_config(page_title="AcademicSync", layout="wide")
st.title("AcademicSync")
st.caption("Multi-agent syllabus ingestion and calendar orchestration (LangGraph + Pydantic + Human-in-the-Loop)")


@st.cache_resource
def get_graph():
    return build_graph()


graph = get_graph()
START_COL = "Start (YYYY-MM-DD HH:MM)"

with st.sidebar:
    sem_start = st.date_input("Semester start date", value=date(2026, 8, 10),
                              help="Only used to convert 'Week N' deadlines into dates.")
    st.markdown(f"Calendar mode: **{'LIVE (Google Calendar)' if gcal_tool.is_live() else 'MOCK'}**")
    st.markdown("Daily study cap: **3 h**  \nMax re-plan loops: **3**")


def read_text(f) -> str:
    if f.name.lower().endswith(".pdf"):
        return "\n".join((p.extract_text() or "") for p in PdfReader(f).pages)
    return f.read().decode("utf-8", errors="ignore")


uploaded = st.file_uploader("Upload a syllabus (.pdf or .txt)", type=["pdf", "txt"])

if st.button("Generate study plan", disabled=uploaded is None):
    with st.spinner("Parser -> Planner -> Auditor running..."):
        try:
            st.session_state.result = graph.invoke({
                "syllabus_text": read_text(uploaded), "semester_start": sem_start.isoformat(),
                "audit_iteration_count": 0, "user_approved": False})
            st.session_state.pop("dispatch", None)
        except Exception as e:
            st.session_state.pop("result", None)
            st.error(f"Could not build the plan: {e}")

res = st.session_state.get("result")
if res:
    c1, c2, c3 = st.columns(3)
    c1.metric("Deliverables found", len(res["parsed_syllabus"]["items"]))
    c2.metric("Re-plan loops used", res.get("audit_iteration_count", 0))
    c3.metric("Conflicts remaining", len(res.get("conflict_details", [])))

    st.subheader("1. Extracted deliverables")
    st.dataframe(pd.DataFrame(res["parsed_syllabus"]["items"]))

    if res.get("conflict_details"):
        st.warning("Some conflicts could not be auto-resolved within 3 loops. Edit the dates below.")
        for msg in res.get("conflicts_detected", []):
            st.write("- " + msg)

    st.subheader("2. Review gate: edit, approve or reject each study block")
    rows = [{"Approve": True, "Course": m["course"], "Milestone": m["title"],
             START_COL: m["start"], "Hours": m["hours"]} for m in res["proposed_milestones"]]
    edited = st.data_editor(pd.DataFrame(rows), disabled=["Course", "Milestone"], key="editor")

    if st.button("Confirm & Sync to Calendar", type="primary"):
        approved = []
        try:
            for (_, r), m in zip(edited.iterrows(), res["proposed_milestones"]):
                if r["Approve"]:
                    datetime.strptime(str(r[START_COL]), FMT)
                    approved.append({**m, "start": str(r[START_COL]), "hours": float(r["Hours"])})
        except ValueError:
            st.error("Use the date format YYYY-MM-DD HH:MM (e.g. 2026-10-12 18:00).")
            st.stop()
        if not approved:
            st.warning("No study blocks approved.")
            st.stop()
        left = find_conflicts(approved, res.get("free_busy_slots", []))
        if left:
            st.error("Your edits still have conflicts:\n\n" + "\n".join("- " + c["detail"] for c in left))
            st.stop()
        st.session_state.dispatch = graph.invoke({**res, "proposed_milestones": approved, "user_approved": True})

out = st.session_state.get("dispatch")
if out:
    st.success(out["dispatch_status"])
    with open(out["ics_path"], "rb") as f:
        st.download_button("Download .ics file", f.read(), file_name="academic_schedule.ics", mime="text/calendar")
