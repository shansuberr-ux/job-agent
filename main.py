import os
import html
import json
import urllib.parse
import requests
from jobspy import scrape_jobs
import pandas as pd
from lanes_data import LANES, PRIMARY_LOCATIONS, TARGET_TITLES, STYLE_GUIDE

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

SEEN_JOBS_FILE = "seen_jobs.json"


def load_state():
    default_state = {
        "seen": set(),
        "last_update_id": 0,
        "custom_query": "",
        "empty_runs": 0,
        "daily_scanned": 0,
        "daily_filtered": 0,
    }
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    default_state["seen"] = set(data)
                    return default_state
                return {
                    "seen": set(data.get("seen", [])),
                    "last_update_id": int(data.get("last_update_id", 0)),
                    "custom_query": data.get("custom_query", ""),
                    "empty_runs": int(data.get("empty_runs", 0)),
                    "daily_scanned": int(data.get("daily_scanned", 0)),
                    "daily_filtered": int(data.get("daily_filtered", 0)),
                }
        except Exception as e:
            print("State read error:", e)
    return default_state


def save_state(state):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(
            {
                "seen": list(state["seen"]),
                "last_update_id": state["last_update_id"],
                "custom_query": state.get("custom_query", ""),
                "empty_runs": state.get("empty_runs", 0),
                "daily_scanned": state.get("daily_scanned", 0),
                "daily_filtered": state.get("daily_filtered", 0),
            },
            f,
            indent=2,
        )


def send_telegram_message(text, use_html=True):
    msg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text[:4000],
        "disable_web_page_preview": True,
    }
    if use_html:
        payload["parse_mode"] = "HTML"

    try:
        resp = requests.post(msg_url, json=payload, timeout=20)
        print("Telegram Status:", resp.status_code, resp.text[:150])
        if resp.status_code == 400 and use_html:
            payload.pop("parse_mode", None)
            resp = requests.post(msg_url, json=payload, timeout=20)
        return resp.ok
    except Exception as e:
        print("Telegram Send Error:", e)
        return False


def send_telegram_alert(text, resume_filename):
    send_telegram_message(text, use_html=True)
    pdf_path = os.path.join("resumes", resume_filename)
    if os.path.exists(pdf_path):
        doc_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        try:
            with open(pdf_path, "rb") as f:
                requests.post(
                    doc_url,
                    data={"chat_id": TELEGRAM_CHAT_ID},
                    files={"document": f},
                    timeout=30,
                )
        except Exception as e:
            print("Telegram PDF Error:", e)


def fetch_all_jobs(custom_query=""):
    all_jobs = []
    search_term = custom_query if custom_query else "Mechanical Design Engineer OR CAE Engineer OR FEA Engineer"

    print(f"Scraping LinkedIn & Indeed India for: {search_term}...")
    try:
        df = scrape_jobs(
            site_name=["linkedin", "indeed"],
            search_term=search_term,
            location="India",
            results_wanted=15,
            hours_old=48,
            country_indeed="india",
            linkedin_fetch_description=True,
        )
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                all_jobs.append(
                    {
                        "id": str(row.get("id") or row.get("job_url")),
                        "title": str(row.get("title") or "Mechanical Engineer"),
                        "organization": str(row.get("company") or "Company"),
                        "location": str(row.get("location") or "India"),
                        "url": str(row.get("job_url") or "#"),
                        "description": str(row.get("description") or ""),
                        "source": str(row.get("site") or "jobspy").upper(),
                    }
                )
            print(f"JobSpy found {len(all_jobs)} jobs from LinkedIn/Indeed!")
    except Exception as e:
        print("JobSpy scrape error:", e)

    if RAPIDAPI_KEY:
        try:
            r = requests.get(
                "https://active-jobs-db.p.rapidapi.com/active-ats",
                headers={
                    "accept": "application/json",
                    "x-rapidapi-key": RAPIDAPI_KEY,
                    "x-rapidapi-host": "active-jobs-db.p.rapidapi.com",
                },
                params={
                    "time_frame": "24h",
                    "limit": "10",
                    "offset": "0",
                    "description_format": "text",
                    "title": '"Mechanical Engineer" OR "Design Engineer" OR "CAE Engineer" OR "FEA"',
                    "location": '"India"',
                },
                timeout=20,
            )
            if r.status_code == 200:
                data = r.json()
                r_jobs = data if isinstance(data, list) else data.get("data", data.get("jobs", []))
                for j in r_jobs:
                    all_jobs.append(
                        {
                            "id": str(j.get("id") or j.get("url")),
                            "title": str(j.get("title") or "Mechanical Engineer"),
                            "organization": str(j.get("organization") or j.get("company") or "Company"),
                            "location": str(j.get("locations_derived") or j.get("location") or "India"),
                            "url": str(j.get("url") or "#"),
                            "description": str(j.get("description_text") or j.get("description") or ""),
                            "source": "RAPIDAPI-ATS",
                        }
                    )
                print(f"RapidAPI added {len(r_jobs)} jobs.")
            else:
                print("RapidAPI status:", r.status_code)
        except Exception as e:
            print("RapidAPI error:", e)

    return all_jobs


def build_networking_links(company, city, lane_key):
    clean_city = city.split(",")[0].strip("[]'\" ") if city else "India"
    queries = {
        "Peer (Mech/Design Eng)": f'site:linkedin.com/in "{company}" ("Mechanical Engineer" OR "Design Engineer" OR "CAE Engineer") "{clean_city}"',
        "Senior (Lead/Manager)": f'site:linkedin.com/in "{company}" ("Mechanical Lead" OR "Engineering Manager" OR "Head of Mechanical" OR "R&D Manager") "{clean_city}"',
        "Recruiter (Talent Acq)": f'site:linkedin.com/in "{company}" ("Talent Acquisition" OR "Technical Recruiter" OR "HR") "{clean_city}"',
    }
    links = {}
    for role, q in queries.items():
        google_url = "https://www.google.com/search?q=" + urllib.parse.quote(q)
        role_kw = "Mechanical Engineer" if "Peer" in role else ("Engineering Manager" if "Senior" in role else "Talent Acquisition")
        li_kw = f"{company} {clean_city} {role_kw}"
        li_url = "https://www.linkedin.com/search/results/people/?keywords=" + urllib.parse.quote(li_kw)
        links[role] = (google_url, li_url)
    return links


def classify_and_tailor(company, title, location, description):
    models_to_try = ["gemini-2.5-flash", "gemini-3.5-flash-lite"]
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    lane_keys_str = ", ".join(list(LANES.keys()))
    prompt = (
        "You are assisting Shanmugam Subramanian, a Mechanical & CAE Engineer (Bachelor's degree, ~3.5 years experience).\n"
        f"Job Posting:\nCompany: {company}\nTitle: {title}\nLocation: {location}\n"
        f"Description: {description[:3000]}\n\n"
        f"Available Lanes: {lane_keys_str}\n\n"
        "CRITICAL FILTER RULES:\n"
        "1. Set 'skip' to true ONLY if the job strictly requires a Mandatory Master's/PhD degree (with no Bachelor's option) OR strictly requires a minimum of 5+ years of experience (e.g., '5-8 years', 'minimum 6 years').\n"
        "2. Extract 'exp_required' (e.g. '2-4 years' or 'Not specified').\n"
        "3. Pick the best matching 'lane' from Available Lanes.\n"
        "4. Write a short phrase (under 15 words) for 'jd_hook'.\n"
        "5. Identify 2 specific technical gaps in 'specific_gaps'.\n\n"
        'Respond STRICTLY in valid JSON with keys: "skip", "skip_reason", "exp_required", "lane", "jd_hook", "specific_gaps".'
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                text_out = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_out)
        except Exception as e:
            print("Error calling model:", model_name, e)

    return {
        "skip": False,
        "skip_reason": "",
        "exp_required": "Check JD",
        "lane": "consumer",
        "jd_hook": "mechanical design, simulation, and DFM",
        "specific_gaps": "Review core JD requirements.",
    }


def main():
    print("--- Starting Shan Job Scout Agent ---")
    state = load_state()
    custom_q = os.getenv("CUSTOM_QUERY", "").strip() or state.get("custom_query", "")

    jobs = fetch_all_jobs(custom_q)
    state["daily_scanned"] += len(jobs)

    new_count = 0
    filtered_this_run = 0

    for job in jobs:
        job_id = job["id"]
        if not job_id or job_id in state["seen"]:
            continue

        title = job["title"]
        company = job["organization"]
        location = job["location"]
        url = job["url"]
        desc = job["description"]
        source = job.get("source", "WEB")

        analysis = classify_and_tailor(company, title, location, desc)
        state["seen"].add(job_id)

        if analysis.get("skip", False):
            filtered_this_run += 1
            print(f"Filtered out (Exp > 4.5y / Master's): {title} at {company}")
            continue

        new_count += 1
        lane_key = analysis.get("lane", "consumer")
        if lane_key not in LANES:
            lane_key = "consumer"
        lane_info = LANES[lane_key]

        loc_lower = location.lower()
        is_primary = any(city in loc_lower for city in PRIMARY_LOCATIONS)
        loc_flag = f"PRIMARY ({location})" if is_primary else f"SECONDARY ({location})"

        subject = lane_info["subject"].format(company=company)
        peer_note = lane_info["note_template"].format(
            name="[Name]", company=company, title=title, jd_hook=analysis.get("jd_hook", "mechanical design")
        )
        hr_note = (
            f"Hi [HR Name],\n\n"
            f"I came across the {title} opening at {company}. With 3.5+ years of hands-on experience in NPD/NPI, "
            f"IP68 enclosure design, and structural FEA/CFD simulation, my background aligns closely with your team's needs.\n\n"
            f"I have attached my tailored resume ({lane_info['resume']}), and you can reach me at shan.sub.err@gmail.com.\n\n"
            f"Would you have 15 minutes this week for a brief discussion?\n\n"
            f"Best regards,\nShanmugam Subramanian"
        )

        net_links = build_networking_links(company, location, lane_key)
        net_lines = [f"- <b>{role}:</b> <a href='{g_url}'>Google X-Ray</a> | <a href='{l_url}'>LinkedIn Search</a>" for role, (g_url, l_url) in net_links.items()]
        net_text = "\n".join(net_lines)

        telegram_msg = (
            f"<b>JOB #{new_count} [{source}]</b>\n"
            f"<b>Company:</b> {html.escape(company)}\n"
            f"<b>Role:</b> {html.escape(title)}\n"
            f"<b>Exp Required:</b> {html.escape(str(analysis.get('exp_required', 'Check JD')))}\n"
            f"<b>Location:</b> {html.escape(loc_flag)}\n"
            f"<b>Lane:</b> {lane_info['name']} (<code>{lane_info['resume']}</code>)\n"
            f"<a href='{url}'>Direct Link to Apply</a>\n\n"
            f"<b>Scout People (No Login):</b>\n{net_text}\n\n"
            f"<b>1. Peer / Manager Draft:</b>\n"
            f"<b>Subject:</b> <code>{html.escape(subject)}</code>\n"
            f"<pre>{html.escape(peer_note)}</pre>\n\n"
            f"<b>2. HR / Recruiter Draft:</b>\n"
            f"<pre>{html.escape(hr_note)}</pre>\n\n"
            f"<b>JD Gaps & Prep:</b>\n{html.escape(str(analysis.get('specific_gaps')))}\n"
            f"{html.escape(lane_info['revise'])}"
        )

        send_telegram_alert(telegram_msg, lane_info["resume"])
        if new_count >= 6:
            break

    state["daily_filtered"] += filtered_this_run

    if new_count > 0:
        state["empty_runs"] = 0
        state["daily_scanned"] = 0
        state["daily_filtered"] = 0
    else:
        state["empty_runs"] += 1
        if state["empty_runs"] >= 6:
            send_telegram_message(
                f"<b>24-Hour Job Scout Summary:</b>\n"
                f"No new matching roles (&lt;4.5 yrs exp, Bachelor's) were found across the last 6 scans (24 hrs).\n"
                f"• Total postings checked today: {state['daily_scanned']}\n"
                f"• Filtered out (Senior/Master's): {state['daily_filtered']}"
            )
            state["empty_runs"] = 0
            state["daily_scanned"] = 0
            state["daily_filtered"] = 0

    save_state(state)
    print(f"--- Finished Run. Sent {new_count} relevant alerts. ---")


if __name__ == "__main__":
    main()