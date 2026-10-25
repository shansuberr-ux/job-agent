# main.py
import os
import time
import json
import urllib.parse
import requests
from lanes_data import LANES, PRIMARY_LOCATIONS, TARGET_TITLES, STYLE_GUIDE

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

SEEN_JOBS_FILE = "seen_jobs.json"
CACHE_FILE = "cached_jobs.json"
CACHE_MAX_AGE_SECONDS = 20 * 3600  # 20 hours


def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, "r") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"⚠️ Could not read {SEEN_JOBS_FILE}: {e}")
    return set()


def save_seen_jobs(seen):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f, indent=2)


def send_telegram_message(text):
    """Sends a text message to Telegram and logs the exact response."""
    msg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(
            msg_url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
        print(f"Telegram Message Status: {resp.status_code} | {resp.text[:150]}")
        return resp.ok
    except Exception as e:
        print(f"❌ Telegram Send Error: {e}")
        return False


def send_telegram_alert(text, resume_filename):
    """Sends the formatted job package and attaches the right PDF resume."""
    send_telegram_message(text)

    pdf_path = os.path.join("resumes", resume_filename)
    if os.path.exists(pdf_path):
        doc_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        try:
            with open(pdf_path, "rb") as f:
                resp = requests.post(
                    doc_url,
                    data={"chat_id": TELEGRAM_CHAT_ID},
                    files={"document": f},
                    timeout=30,
                )
                print(f"Telegram PDF Upload ({resume_filename}) Status: {resp.status_code}")
        except Exception as e:
            print(f"❌ Telegram PDF Upload Error: {e}")
    else:
        print(f"⚠️ Warning: Resume file not found at {pdf_path}. Check your resumes/ folder.")


def build_networking_links(company, city, lane_key):
    """Generates safe Google X-Ray and LinkedIn search links without logging in."""
    clean_city = city.split(",")[0].strip("[]'\" ") if city else "India"

    queries = {
        "Peer (Mech/Design Eng)": f'site:linkedin.com/in "{company}" ("Mechanical Engineer" OR "Design Engineer" OR "CAE Engineer") "{clean_city}"',
        "Senior (Lead/Manager)": f'site:linkedin.com/in "{company}" ("Mechanical Lead" OR "Engineering Manager" OR "Head of Mechanical" OR "R&D Manager") "{clean_city}"',
        "Recruiter (Talent Acq)": f'site:linkedin.com/in "{company}" ("Talent Acquisition" OR "Technical Recruiter" OR "HR") "{clean_city}"',
    }

    links = {}
    for role, q in queries.items():
        google_url = f"https://www.google.com/search?q={urllib.parse.quote(q)}"
        li_kw = f"{company} {clean_city} " + (
            "Mechanical Engineer"
            if "Peer" in role
            else "Engineering Manager"
            if "Senior" in role
            else "Talent Acquisition"
        )
        li_url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(li_kw)}"
        links[role] = (google_url, li_url)
    return links


def fetch_jobs():
    """Returns cached jobs if fresh (<20h old) to save RapidAPI quota during testing."""
    if os.path.exists(CACHE_FILE):
        file_age = time.time() - os.path.getmtime(CACHE_FILE)
        if file_age < CACHE_MAX_AGE_SECONDS:
            try:
                with open(CACHE_FILE, "r") as f:
                    cached = json.load(f)
                if cached:
                    print(f"♻️ Using {len(cached)} cached jobs from {CACHE_FILE} (0 RapidAPI quota used!)")
                    return cached
            except Exception as e:
                print(f"⚠️ Cache read error, fetching fresh: {e}")

    url = "https://active-jobs-db.p.rapidapi.com/active-ats"
    headers = {
        "accept": "application/json",
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "active-jobs-db.p.rapidapi.com",
    }
    params = {
        "time_frame": "24h",
        "limit": "10",
        "offset": "0",
        "description_format": "text",
        "title": '"Mechanical Engineer" OR "Design Engineer" OR "CAE Engineer" OR "FEA" OR "CFD" OR "R&D Engineer" OR "Product Design"',
        "location": '"India"',
    }

    print(f"Fetching fresh jobs from {url}...")
    try:
        r = requests.get(url, headers=headers, params=params, timeout=25)
        print(f"RapidAPI Status Code: {r.status_code}")
        if r.status_code != 200:
            print(f"⚠️ RapidAPI Error Body: {r.text[:300]}")
        r.raise_for_status()
        data = r.json()
        jobs_list = data if isinstance(data, list) else data.get("data", data.get("jobs", []))
        print(f"✅ Success! Total jobs returned by RapidAPI: {len(jobs_list)}")

        if jobs_list:
            with open(CACHE_FILE, "w") as f:
                json.dump(jobs_list, f, indent=2)
        return jobs_list
    except Exception as e:
        print(f"❌ API Fetch Error: {e}")
        return []


def classify_and_tailor(company, title, location, description):
    """Calls Gemini 3 / 2.5 series via REST API with automatic model fallback."""
    models_to_try = [
        "gemini-3.8-flash",
        "gemini-3.1-pro-preview",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash",
    ]

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
    }

    prompt = f"""
You are assisting Shanmugam Subramanian, a Mechanical & CAE Engineer.
Writing Style Guide: {STYLE_GUIDE}

Job Posting:
Company: {company}
Title: {title}
Location: {location}
Description: {description[:3500]}

Available Lanes: {list(LANES.keys())}

Tasks:
1. Pick the single best matching lane key from Available Lanes.
2. Write the short phrase (under 15 words) that replaces {{jd_hook}} in his cover note (e.g., "sensor enclosure design with IP sealing, tolerance stack-up and thermal protection").
3. Identify 2 specific technical gaps between the Job Description and Shan's background, and suggest 1 concrete revision topic.

Respond STRICTLY in valid JSON with keys: "lane", "jd_hook", "specific_gaps".
"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                res_json = r.json()
                text_out = res_json["candidates"][0]["content"]["parts"][0]["text"]
                print(f"✅ Tailored with {model_name}")
                return json.loads(text_out)
            else:
                print(f"⚠️ {model_
