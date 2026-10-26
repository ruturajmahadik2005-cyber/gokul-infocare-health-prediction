from __future__ import annotations

import os
import re
import secrets
import sqlite3
import time
from datetime import date, datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "patients.db"))
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

TEST_CASES = [
    {"name":"Robyn Pears","dob":"28.01.1960","email":"robyn@gmail.com","glucose":"232","haemoglobin":"13.5","cholesterol":"180"},
    {"name":"John Hunter","dob":"10.12.1990","email":"hunter@gmail","glucose":"94","haemoglobin":"15","cholesterol":"200"},
    {"name":"Darryl Tim","dob":"12.11.1993","email":"timd@smh.com.au","glucose":"240","haemoglobin":"18.6","cholesterol":"326"},
    {"name":"Peter Larry","dob":"31.11.2001","email":"Larry@hotmail.com","glucose":"88","haemoglobin":"11.5","cholesterol":"165"},
    {"name":"Sam Kerr","dob":"09.12.2006","email":"sam@news.com.au","glucose":"198","haemoglobin":"8.9","cholesterol":"192"},
    {"name":"Robyn Pears","dob":"28.01.1960","email":"robyn@gmail.com","glucose":"232","haemoglobin":"13.5","cholesterol":"180"},
    {"name":"Madison XI","dob":"12.09.1998","email":"madison@hotmail.com","glucose":"85","haemoglobin":"7.6","cholesterol":"163"},
    {"name":"Kris Wu","dob":"19.10.2030","email":"Kris.wu.gmail.com","glucose":"79","haemoglobin":"16.5","cholesterol":"197"},
    {"name":"Tenille Singh","dob":"30.11.1991","email":"Tenille@yahoo.com","glucose":"101","haemoglobin":"15","cholesterol":"310"},
    {"name":"Prem Kumar","dob":"28.04.1990","email":"prem@telstra.com","glucose":"155","haemoglobin":"12.5","cholesterol":"265"},
]

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS patients (
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, dob TEXT NOT NULL,
      email TEXT NOT NULL COLLATE NOCASE UNIQUE, glucose REAL NOT NULL,
      haemoglobin REAL NOT NULL, cholesterol REAL NOT NULL, remarks TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    return db

def validate(data, existing_id=None):
    errors=[]
    name=data.get("name", "").strip()
    if len(name)<2 or len(name)>100: errors.append("Full name must be 2–100 characters.")
    try:
        dob=datetime.strptime(data.get("dob", ""), "%d/%m/%Y").date()
        if dob > date.today(): errors.append("Date of birth cannot be in the future.")
    except ValueError: errors.append("Date of birth must be a real date in dd/mm/yyyy format.")
    email=data.get("email", "").strip()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email): errors.append("Enter a valid email address (for example, name@example.com).")
    values={}
    for key,label,low,high in [("glucose","Glucose",0,1000),("haemoglobin","Haemoglobin",0,100),("cholesterol","Cholesterol",0,2000)]:
        try:
            v=float(data.get(key,""))
            if not 0 < v <= high: errors.append(f"{label} must be greater than 0 and no more than {high}.")
            else: values[key]=v
        except (ValueError,TypeError): errors.append(f"{label} must be numeric.")
    if not errors:
        with connect() as db:
            q="SELECT id FROM patients WHERE email=? COLLATE NOCASE"; args=[email]
            row=db.execute(q,args).fetchone()
            if row and row["id"] != existing_id: errors.append("A record with this email already exists. Exact duplicate records are not created.")
    if errors: return None,errors
    return {"name":name,"dob":dob.isoformat(),"email":email,**values},[]

def ai_remarks(patient):
    disclaimer="Educational screening note only; not a diagnosis. Discuss results with a qualified health professional."
    provider=os.getenv("AI_PROVIDER", "gemini").strip().lower()
    prompt=(f"Provide a concise, cautious, non-diagnostic educational note using only these test values: glucose {patient['glucose']}, "
            f"haemoglobin {patient['haemoglobin']}, cholesterol {patient['cholesterol']}. "
            "Give a cautious screening observation and, when justified, name the possible health condition or disease risk the values might warrant discussing, "
            "but do not diagnose a disease, calculate a probability, or recommend treatment. Units, fasting status and lab ranges are unknown, "
            "so state that values alone cannot establish risk and ask the reader to consult a qualified health professional. Keep under 60 words.")
    if provider == "gemini":
        key=os.getenv("GEMINI_API_KEY", "")
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        endpoint=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        if not key:
            return f"Gemini API is not configured; no prediction was made. Add GEMINI_API_KEY in your local .env file. {disclaimer}"
        try:
            payload={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.2,"maxOutputTokens":120}}
            for attempt in range(3):
                try:
                    response=requests.post(endpoint,headers={"x-goog-api-key":key},json=payload,timeout=(8,15))
                except (requests.Timeout,requests.ConnectionError):
                    if attempt == 2:
                        raise
                    time.sleep(1 + attempt * 2)
                    continue
                if response.status_code not in (429,503) or attempt == 2:
                    break
                time.sleep(1 + attempt * 2)
            response.raise_for_status()
            parts=response.json()["candidates"][0]["content"]["parts"]
            note=" ".join(part.get("text","") for part in parts).strip()
            if not note:
                raise ValueError("Empty response from Gemini")
            return f"{note} {disclaimer}"
        except (requests.RequestException,KeyError,ValueError,TypeError) as exc:
            app.logger.warning("Gemini API call failed (%s): %s", type(exc).__name__, exc)
            return f"AI service is unavailable; no AI prediction was made. {disclaimer}"
    if provider == "openai":
        endpoint=os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
        key=os.getenv("AI_API_KEY", "")
        model=os.getenv("AI_MODEL", "gpt-6-luna")
        if not key:
            return f"OpenAI API is not configured; no prediction was made. Configure AI_API_KEY in .env. {disclaimer}"
        try:
            response=requests.post(endpoint,headers={"Authorization":f"Bearer {key}"},json={"model":model,"messages":[{"role":"user","content":prompt}],"temperature":0.2},timeout=12)
            response.raise_for_status()
            note=response.json()["choices"][0]["message"]["content"].strip()
            return f"{note} {disclaimer}"
        except (requests.RequestException,KeyError,ValueError,TypeError) as exc:
            app.logger.warning("OpenAI API call failed (%s): %s", type(exc).__name__, exc)
            return f"AI service is unavailable; no AI prediction was made. {disclaimer}"
    return f"Unknown AI provider '{provider}'; set AI_PROVIDER to gemini or openai. {disclaimer}"

@app.get("/")
def index():
    with connect() as db:
        patients=db.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
    return render_template("index.html",patients=patients)

@app.post("/patients")
def create_patient():
    data,errors=validate(request.form)
    if errors:
        for error in errors: flash(error,"error")
        return redirect(url_for("index"))
    data["remarks"]=ai_remarks(data)
    try:
        with connect() as db:
            db.execute("INSERT INTO patients(name,dob,email,glucose,haemoglobin,cholesterol,remarks) VALUES(:name,:dob,:email,:glucose,:haemoglobin,:cholesterol,:remarks)",data)
        flash("Patient record saved.","success")
    except sqlite3.IntegrityError: flash("A record with this email already exists.","error")
    return redirect(url_for("index"))

@app.post("/patients/<int:patient_id>/update")
def update_patient(patient_id):
    data,errors=validate(request.form,patient_id)
    if errors:
        for error in errors: flash(error,"error")
        return redirect(url_for("index"))
    data["remarks"]=ai_remarks(data)
    with connect() as db:
        cur=db.execute("UPDATE patients SET name=:name,dob=:dob,email=:email,glucose=:glucose,haemoglobin=:haemoglobin,cholesterol=:cholesterol,remarks=:remarks WHERE id=:id",{**data,"id":patient_id})
    flash("Record updated." if cur.rowcount else "Record not found.","success" if cur.rowcount else "error")
    return redirect(url_for("index"))

@app.post("/patients/<int:patient_id>/delete")
def delete_patient(patient_id):
    with connect() as db: cur=db.execute("DELETE FROM patients WHERE id=?",(patient_id,))
    flash("Record deleted." if cur.rowcount else "Record not found.","success" if cur.rowcount else "error")
    return redirect(url_for("index"))

@app.post("/demo/import")
def import_demo():
    accepted=[]; rejected=[]
    for number,raw in enumerate(TEST_CASES,1):
        data={**raw,"dob":raw["dob"].replace(".","/")}
        # Assignment supplies dates as dd.mm.yyyy; normalize only for parsing, preserving table values.
        try: data["dob"]=datetime.strptime(raw["dob"],"%d.%m.%Y").strftime("%d/%m/%Y")
        except ValueError: data["dob"]=raw["dob"]
        clean,errors=validate(data)
        if errors: rejected.append((number,errors)); continue
        clean["remarks"]=ai_remarks(clean)
        try:
            with connect() as db: db.execute("INSERT INTO patients(name,dob,email,glucose,haemoglobin,cholesterol,remarks) VALUES(:name,:dob,:email,:glucose,:haemoglobin,:cholesterol,:remarks)",clean)
            accepted.append(number)
        except sqlite3.IntegrityError: rejected.append((number,["Duplicate email matches an existing record; duplicate not inserted."]))
    if accepted: flash(f"Imported test cases: {', '.join(map(str,accepted))}.","success")
    for n,errs in rejected: flash(f"Test #{n} not inserted: {' '.join(errs)}","error")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower()=="true")
