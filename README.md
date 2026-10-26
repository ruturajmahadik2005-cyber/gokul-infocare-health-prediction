# Gokul Infocare · Patient Health Records

A Python and Flask coursework app for the Task 2 patient blood-test scenario. It provides validated create, read, update and delete actions, SQLite persistence, and optional AI-generated educational screening remarks.

## Run locally

1. Install Python 3.10 or later.
2. In PowerShell, create and activate a virtual environment, then install dependencies:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`. For the Gemini free tier, set `AI_PROVIDER=gemini` and put your Google AI Studio key after `GEMINI_API_KEY=`. Keep `.env` private and never commit it. AI provider quotas and availability can change; without a working API key, the app still runs and displays a clear no-prediction message.
4. Start the app with `python app.py` and open http://127.0.0.1:5000.

SQLite creates `patients.db` on first run. Both `.env` and database files are excluded from Git by `.gitignore`.

## Assignment test data

Choose **Load assignment test cases** once from an empty database. The importer preserves the supplied values and reports validation results without silently correcting the source rows. Test cases #1, #3, #5, #7, #9 and #10 are valid unique records. Test #2 has an incomplete email, #4 has an impossible date (31.11.2001), and #8 has a future date and malformed email. Test #6 duplicates test #1 and is skipped by the case-insensitive unique-email rule.

Avoid reloading after editing or deleting assignment records: a changed email can allow its original source row to be imported again. To start a fresh demonstration, stop the app and move the local `patients.db` out of the project folder, restart the app, and load the test cases once. The assignment source data is not changed by the importer.

## Validation and record behavior

- Names must contain 2–100 characters.
- Dates must be real dates in `dd/mm/yyyy` format and cannot be in the future.
- Email addresses must have a local part and a dotted domain.
- Glucose, haemoglobin and cholesterol must be numeric and within broad positive input bounds.
- Email addresses are unique without regard to case.
- Database writes use parameterized SQL. AI API failures do not prevent local record creation or updates.

## AI integration and health limits

The app defaults to Google's Gemini Developer API using `gemini-3.8-flash`. The external request sends only glucose, haemoglobin and cholesterol; it does not send the patient's name, date of birth or email. Configure `GEMINI_API_KEY` locally in `.env`. The free tier has model and usage limits, which may change, and Google may use free-tier prompts to improve its products. Do not submit identifiable or real patient health data without appropriate consent.

The prompt requests a cautious educational screening observation and possible health concern, not a diagnosis, probability or treatment recommendation. Units, fasting status and laboratory reference ranges are not collected, so the result is limited and not a diagnostic or clinical decision tool. Every AI remark includes a clinician-review disclaimer. An OpenAI-compatible provider is also supported by setting `AI_PROVIDER=openai` and its credentials in `.env`; OpenAI API billing is separate from ChatGPT subscriptions.

## Code walkthrough

- `app.py`: Flask routes, SQLite schema, validation, assignment importer, AI API calls and error handling.
- `templates/index.html`: entry form, records table, edit dialog and status messages.
- `static/style.css`: responsive visual design.
- `.env.example`: configuration names only; it contains no credentials.

## Video walkthrough plan

1. Show the empty state and entry form.
2. Load the assignment rows once. Explain the errors in #2, #4 and #8, and the duplicate #6.
3. Show the six valid unique records and an AI remark. Explain the SQLite storage and validation.
4. Edit one valid record's email to `gokul@infocare.com` and show the saved row.
5. Delete one record and show the updated list.
6. Walk through `validate()`, `ai_remarks()` and the CRUD routes. Show `.env.example`, not `.env` or any API key.
7. State that remarks are educational only and not medical advice.

Before recording, reset the demo database and load the assignment rows once. Do not reload after editing or deleting. Submit the candidate details, GitHub repository link and video link together in one email as requested by the assignment.
