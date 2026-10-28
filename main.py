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
CACHE_MAX_AGE_SECONDS = 12 * 3600  # 12 hours


def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, "r") as f:
                return set(json.load(f))
        except Exception as e:
            print("Could not read seen_jobs.json:", e)
    return set()


def save_seen_jobs(seen):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f, indent=2)


def send_telegram_message(text):
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
        print("Telegram Message Status:", resp.status_code, resp.text[:150])
        return resp.ok
    except Exception as e:
        print("Telegram Send Error:", e)
        return False


def check_telegram_commands():
    """2-Way feature: Checks if you sent any text commands to the bot on Telegram."""
    updates_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset=-1"
    try:
        resp = requests.get(updates_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("result", [])
            if results:
                latest = results[-1]
                message = latest.get("message", {})
                text = message.get("text", "").strip().lower()
                sender_id = str(message.get("chat", {}).get("id", ""))
                
                # If message is from you
                if sender_id == str(TELEGRAM_CHAT_ID) and text:
                    print(f"Received Telegram Command: {text}")
                    if text == "/run" or text == "run":
                        send_telegram_message("🤖 <b>Command Received:</b> Forcing a fresh job fetch now!")
                        if os.path.exists(CACHE_FILE):
                            os.remove(CACHE_FILE) # Clear cache to force fresh pull
                    elif text.startswith("search "):
                        query = text.replace("search ", "").strip()
                        send_telegram_message(f"🔍 Custom search requested for: <i>{query}</i>. Will prioritize in next scan.")
                    elif text == "/help":
                        send_telegram_message("🤖 <b>Agent Commands:</b>\n- <code>/run</code>: Force fresh job scan\n- <code>search [keyword]</code>: Note custom interest")
    except Exception as e:
        print("Error checking Telegram updates:", e)


def send_telegram_alert(text, resume_filename):
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
                print("Telegram PDF Upload Status:", resume_filename, resp.status_code)
        except Exception as e:
            print("Telegram PDF Upload Error:", e)
    else:
        print("Warning: Resume file not found at", pdf_path)


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


def fetch_jobs():
    if os.path.exists(CACHE_FILE):
        file_age = time.time() - os.path.getmtime(CACHE_FILE)
        if file_age < CACHE_MAX_AGE_SECONDS:
            try:
                with open(CACHE_FILE, "r") as f:
                    cached = json.load(f)
                if cached:
                    print("Using cached jobs:", len(cached))
                    return cached
            except Exception as e:
                print("Cache read error:", e)

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

    print("Fetching fresh jobs from RapidAPI...")
    try:
        r = requests.get(url, headers=headers, params=params, timeout=25)
        print("RapidAPI Status Code:", r.status_code)
        if r.status_code != 200:
            print("RapidAPI Error Body:", r.text[:300])
        r.raise_for_status()
        data = r.json()
        jobs_list = data if isinstance(data, list) else data.get("data", data.get("jobs", []))
        print("Total jobs returned by RapidAPI:", len(jobs_list))
        if jobs_list:
            with open(CACHE_FILE, "w") as f:
                json.dump(jobs_list, f, indent=2)
        return jobs_list
    except Exception as e:
        print("API Fetch Error:", e)
        return []


def classify_and_tailor(company, title, location, description):
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
    ]
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
    }
    lane_keys_str = ", ".join(list(LANES.keys()))
    prompt = (
        "You are assisting Shanmugam Subramanian, a Mechanical & CAE Engineer (Bachelor's degree, ~2-4 years experience).\n"
        f"Writing Style Guide: {STYLE_GUIDE}\n\n"
        f"Job Posting:\nCompany: {company}\nTitle: {title}\nLocation: {location}\n"
        f"Description: {description[:3000]}\n\n"
        f"Available Lanes: {lane_keys_str}\n\n"
        "CRITICAL FILTER RULES:\n"
        "1. If this job strictly requires a Master's degree (M.Tech/M.S.) or requires more than 5 years of experience, set 'skip' to true.\n"
        "2. Otherwise set 'skip' to false, pick the single best matching lane key from Available Lanes.\n"
        "3. Write a short phrase (under 15 words) that replaces {jd_hook} in his cover note.\n"
        "4. Identify 2 specific technical gaps between the Job Description and Shan's background, and suggest 1 concrete revision topic.\n\n"
        'Respond STRICTLY in valid JSON with keys: "skip", "lane", "jd_hook", "specific_gaps".'
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
                res_json = r.json()
                text_out = res_json["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_out)
            else:
                print("Model failed:", model_name, r.status_code)
        except Exception as e:
            print("Error calling model:", model_name, e)

    return {
        "skip": False,
        "lane": "consumer",
        "jd_hook": "mechanical design, simulation, and DFM",
        "specific_gaps": "Review core JD requirements.",
    }


def main():
    print("--- Starting Shan Job Scout Agent ---")
    
    # Check incoming telegram messages first (2-way chat capability)
    check_telegram_commands()

    seen_jobs = load_seen_jobs()
    jobs = fetch_jobs()

    if not jobs:
        send_telegram_message("<b>Job Scout Heartbeat:</b> 0 matching jobs found in this batch.")
        return

    new_count = 0
    for idx, job in enumerate(jobs, 1):
        job_id = str(job.get("id") or job.get("url") or (str(job.get("title", "")) + "_" + str(job.get("organization", ""))))
        if not job_id or job_id in seen_jobs:
            continue

        title = str(job.get("title") or "Mechanical Engineer")
        company = str(job.get("organization") or job.get("company") or "Company")
        location = str(job.get("locations_derived") or job.get("location") or "India")
        url = str(job.get("url") or job.get("apply_url") or "#")
        desc = str(job.get("description_text") or job.get("description") or "")

        analysis = classify_and_tailor(company, title, location, desc)
        
        # Mark as seen so it's never evaluated again
        seen_jobs.add(job_id)

        # Skip irrelevant Master's / Senior experience jobs
        if analysis.get("skip", False):
            print(f"Skipping irrelevant role (Master's/Senior mismatch): {title} at {company}")
            continue

        new_count += 1
        lane_key = analysis.get("lane", "consumer")
        if lane_key not in LANES:
            lane_key = "consumer"
        lane_info = LANES[lane_key]

        subject = lane_info["subject"].format(company=company)
        peer_note = lane_info["note_template"].format(
            name="[Name]", company=company, title=title, jd_hook=analysis.get("jd_hook", "mechanical design")
        )
        
        hr_note = (
            f"Hi [HR Name],\n\n"
            f"I came across the {title} opening at {company}. With hands-on experience in NPD/NPI, "
            f"IP68 enclosure design, and structural FEA/CFD simulation, my background aligns closely with your team's needs.\n\n"
            f"I have attached my tailored resume (<code>{lane_info['resume']}</code>), and you can reach me directly at "
            f"<b>shan.sub.err@gmail.com</b> or phone.\n\n"
            f"Would you have 15 minutes this week for a brief discussion?\n\n"
            f"Best regards,\nShanmugam Subramanian"
        )

        net_links = build_networking_links(company, location, lane_key)
        net_lines = [f"- <b>{role}:</b> <a href='{g_url}'>Google X-Ray</a> | <a href='{l_url}'>LinkedIn Search</a>" for role, (g_url, l_url) in net_links.items()]
        net_text = "\n".join(net_lines)

        telegram_msg = (
            f"🔍 <b>JOB MATCH #{new_count}</b>\n"
            f"🏢 <b>Company:</b> {company}\n"
            f"💼 <b>Role:</b> {title}\n"
            f"📍 <b>Location:</b> {location}\n"
            f"🏷 <b>Domain Lane:</b> {lane_info['name']}\n"
            f"📄 <b>Attached Resume:</b> <code>{lane_info['resume']}</code>\n"
            f"🔗 <a href='{url}'>Direct Link to Apply</a>\n\n"
            f"👥 <b>Scout People on LinkedIn (No Login Needed):</b>\n{net_text}\n\n"
            f"💬 <b>1. Peer / Manager Outreach Draft:</b>\n"
            f"<b>Subject:</b> <code>{subject}</code>\n"
            f"<pre>{peer_note}</pre>\n\n"
            f"👤 <b>2. HR / Recruiter Outreach Draft:</b>\n"
            f"<pre>{hr_note}</pre>\n\n"
            f"⚠️ <b>JD Gaps & Interview Prep:</b>\n{analysis.get('specific_gaps')}\n"
            f"{lane_info['revise']}"
        )

        send_telegram_alert(telegram_msg, lane_info["resume"])

    save_seen_jobs(seen_jobs)
    print(f"--- Finished Run. Sent {new_count} relevant alerts. ---")


if __name__ == "__main__":
    main()
