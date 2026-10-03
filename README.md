# AcademicSync 🎓📅

> **Autonomous Multi-Agent Academic Syllabus Ingestion & Calendar Orchestration System**

AcademicSync converts unstructured academic syllabi (PDF/TXT) into structured, conflict-free, milestone-spaced study schedules deployed directly to digital calendars (.ics / Outlook / Google Calendar).

---

## Key Features
- **Deterministic Parsing:** Uses Pydantic schemas to validate deliverables, relative weeks, and grading weights.
- **Backward Milestone Spacing:** Generates progressive study blocks weighted by assignment grade contribution.
- **Deterministic Collision Auditing:** Python interval math detects overlaps against student commitments and daily study caps.
- **Local Sovereign AI:** Powered entirely offline using \llama3.1:8b\ via Ollama (no external API keys required).
- **Human-in-the-Loop Review Gate:** Interactive Streamlit dashboard allowing users to edit or reject proposed blocks.
- **Idempotent Calendar Actuation:** Prevents duplicate entries via MD5 event signature hashing.

---

## Quickstart

### 1. Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) with \llama3.1:8b\ pulled:
  \\\ash
  ollama pull llama3.1:8b
  \\\

### 2. Installation
\\\ash
git clone https://github.com/HermesRoe/AcademicSync.git
cd AcademicSync
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
\\\

### 3. Configuration (\.env\)
\\\env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
USE_GCAL=false
\\\

### 4. Running the Tests & App
\\\ash
# Run pytest verification
pytest -q

# Launch Streamlit Interface
streamlit run app.py
\\\

---

## Author
- **Student:** U HARI HARAN (Reg No: 44110234)
- **Institution:** Sathyabama Institute of Science and Technology
