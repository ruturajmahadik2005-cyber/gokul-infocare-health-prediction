# Gokul Infocare · Patient Health Records

A small Python + Flask application for managing the blood test information required in Task 2. It stores records in SQLite, validates inputs, provides create/read/update/delete actions, and can request cautious educational remarks from a configurable external AI API.

## Run locally

1. Install Python 3.10 or later.
2. In this folder, create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`. Keep `AI_API_KEY` blank for offline remarks, or add your own API key locally. Do not commit `.env`.
4. Start the app:

   ```powershell
   python app.py
   ```

5. Open http://127.0.0.1:5000.

SQLite creates `patients.db` the first time the app runs. `DATABASE_PATH` can point to another local path. The built-in remarks clearly state when AI is not configured or unavailable.

## Assignment test data

Choose **Load assignment test cases** to attempt the ten supplied rows. Original names, dates, emails and measurements are retained. Date separators are interpreted for validation only because the assignment table uses dots while the requested form format is `dd/mm/yyyy`.

Valid rows are stored. Invalid data is not silently corrected: the app reports each test number and its reason. Repeating the import reports the duplicate email and skips it. Test 6 duplicates test 1; test 2 has an incomplete email domain; test 4 has an impossible date; test 8 has a future birth date and malformed email. The initial demonstration state in this workspace has Prem Kumar's email changed to `gokul@infocare.com` and Tenille Singh deleted. The final five saved records can be reviewed on startup. To repeat the full demo from a clean database, stop the app, move or remove the local `patients.db`, restart, and choose **Load assignment test cases**; then perform the two actions using the row menus. The import does not modify source data.

## Validation and record behavior

- Names must contain 2–100 characters.
- Birth dates must be real dates in `dd/mm/yyyy` format and cannot be in the future.
- Email addresses need a simple local-part, `@`, and domain with a dot.
- Glucose, haemoglobin and cholesterol must be numeric and within broad positive input bounds.
- Email is unique (case-insensitive), so exact duplicates are rejected clearly.
- Every database write uses parameterized SQL. AI network failures do not prevent local record creation/update.

## AI integration and health limits

The app defaults to the Gemini Developer API. Create a free-tier key in Google AI Studio and set `GEMINI_API_KEY` in the untracked `.env` file. The default model is `gemini-3.8-flash`; free-tier quota and model availability are controlled by Google and can change. Set `AI_PROVIDER=openai` to use the optional OpenAI-compatible integration instead; that requires OpenAI API billing/credits.

The app sends only the three numeric test values to the selected provider, not the patient's name, date of birth or email. On Google's free tier, submitted content may be used to improve its products; do not send identifiable or real patient health data without appropriate consent. The prompt asks for a limited educational screening observation and possible concern while prohibiting diagnoses, probabilities and treatment claims. Units, fasting status and lab reference ranges are not collected, so any note is limited and is not a diagnostic or clinical decision tool. Every returned remark includes a clinician-review disclaimer.

## Code walkthrough

- `app.py`: Flask routes, SQLite schema, validation, test-case importer, AI API request and error handling.
- `templates/index.html`: patient entry form, records table, edit dialog and status feedback.
- `static/style.css`: responsive visual design.
- `.env.example`: configuration names only; it contains no credentials.

## Video walkthrough plan (record locally)

1. Introduce the app and show the clean empty state and entry form.
2. Load the assignment test cases. Explain the accepted rows and why #2 (email), #4 (impossible date), and #8 (future date and malformed email) fail validation. Explain #6 is an exact duplicate of #1 and is skipped by the unique-email rule. Re-import once to demonstrate duplicate handling.
3. Show all persisted records and explain validation, SQLite persistence, and the cautious AI remarks/offline message.
4. Edit one accepted record's email to `gokul@infocare.com`; save and show the updated row.
5. Delete one accepted record, confirm, and show the refreshed list.
6. Walk through `validate()`, `ai_remarks()`, and the CRUD routes in `app.py`. Show `.env.example`, making clear that actual keys stay local and are not part of the GitHub repository.
7. Close by stating that remarks are educational and not medical advice.

Before sharing a GitHub URL or video, create and verify them yourself. This workspace does not claim a repository has been uploaded or a video recorded.
