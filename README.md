# AcademicSync - setup and run guide (about 1-2 hours)

Multi-agent syllabus-to-calendar system: Parser -> Planner -> Auditor (Python intervals + Critic LLM, max 3 loops)
-> Human review gate -> Dispatcher (MD5 idempotent IDs, Google Calendar / .ics).

## 0. What you need
- Python 3.10 or newer (check: `python --version`), internet, an OpenAI API key (platform.openai.com -> API keys).
- Optional (live calendar only): a Google account.

## 1. Install (10 min)
```
cd AcademicSync
python -m venv venv
venv\Scripts\activate            # Windows      (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # Linux/Mac: cp .env.example .env
```
Open `.env` and paste your key after `OPENAI_API_KEY=`. Leave `USE_GCAL=false` for now.

## 2. Run the tests (2 min, no API key needed)
```
pytest -q
```
Expected: `17 passed`. These cover schema validation (test_parser), conflict detection (test_auditor),
the 3-loop cap (test_convergence) and duplicate prevention (test_dispatcher).

## 3. Run the app (5 min)
```
streamlit run app.py
```
1. Upload `data/sample_syllabi/CS101_Syllabus.txt`, keep semester start 10 Aug 2026, click **Generate study plan**.
2. You see: deliverables table, re-plan loops used, conflicts remaining, and the editable review table.
3. Untick or edit any block, then click **Confirm & Sync to Calendar**. Download the `.ics`.
4. Click Confirm a second time: status shows "0 created, N duplicates skipped" (this is test TC3).
5. TAKE SCREENSHOTS: (a) after upload, before Generate = Figure 5.1; (b) review table + success message = Figure 5.2.

To reset the duplicate ledger for a fresh demo, delete `data/dispatched_ids.json`.

## 4. Benchmark on 5 syllabi (30-40 min)
Put 3-5 real syllabi (PDF/TXT) in `data/sample_syllabi/`, run each through the app, and note per syllabus:
fields correct / fields total (check against the syllabus by hand), loops used (metric card), conflicts remaining.
Accuracy = total correct / total fields. Average iterations = sum of loops / number of syllabi.
Save the numbers in `eval_parser.csv`; these are your real results for Chapter 6.

## 5. Optional: live Google Calendar (30 min, skip if short of time)
1. console.cloud.google.com -> new project -> APIs & Services -> Library -> enable **Google Calendar API**.
2. OAuth consent screen -> External -> add your Gmail under **Test users**.
3. Credentials -> Create credentials -> OAuth client ID -> **Desktop app** -> download JSON, rename to `credentials.json`,
   place it in the project root.
4. Set `USE_GCAL=true` in `.env`, restart the app. A browser window asks for consent on first sync; `token.json` is created.
Never upload `.env`, `credentials.json` or `token.json` to GitHub (add them to `.gitignore`).

## 6. Push to GitHub (5 min)
```
git init
echo .env> .gitignore & echo credentials.json>> .gitignore & echo token.json>> .gitignore & echo venv/>> .gitignore
git add . && git commit -m "AcademicSync v1.0.0"
git branch -M main
git remote add origin https://github.com/HermesRoe/AcademicSync.git
git push -u origin main
git tag v1.0.0-release && git push --tags
```

## 7. Troubleshooting
- `ModuleNotFoundError: src` -> run commands from the AcademicSync folder.
- `openai.AuthenticationError` -> wrong or missing key in `.env`.
- `ZoneInfoNotFoundError` on Windows -> `pip install tzdata`.
- Parser returns 0 items -> PDF is a scan (no text layer); use a text PDF or paste into a .txt file.
- Streamlit shows old behaviour -> press R in the browser tab or restart `streamlit run app.py`.

## 8. How the code maps to the report
parser_node.py = Parser (Pydantic extraction, 1000-char chunks); planner_node.py = grade-weighted backward milestones;
interval_engine.py + auditor_node.py = deterministic overlap/3-hour-cap check + Critic LLM message;
dispatcher_node.py = MD5 IDs + Calendar/.ics; graph.py = LangGraph loop; app.py = Streamlit review gate.
