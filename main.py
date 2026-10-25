# main.py
import os
import json
import urllib.parse
import requests
import google.generativeai as genai
from lanes_data import LANES, PRIMARY_LOCATIONS, TARGET_TITLES, STYLE_GUIDE

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

SEEN_JOBS_FILE = "seen_jobs.json"

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_jobs(seen):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f)

def build_networking_links(company, city, lane_key):
    """Generates safe Google X-Ray and LinkedIn search links without logging in."""
    clean_city = city.split(",")[0].strip() if city else "India"
    
    queries = {
        "Peer (Mech/Design Eng)": f'site:linkedin.com/in "{company}" ("Mechanical Engineer" OR "Design Engineer" OR "CAE Engineer") "{clean_city}"',
        "Senior (Lead/Manager)": f'site:linkedin.com/in "{company}" ("Mechanical Lead" OR "Engineering Manager" OR "Head of Mechanical" OR "R&D Manager") "{clean_city}"',
        "Recruiter (Talent Acq)": f'site:linkedin.com/in "{company}" ("Talent Acquisition" OR "Technical Recruiter" OR "HR") "{clean_city}"'
    }
    
    links = {}
    for role, q in queries.items():
        google_url = f"https://www.google.com/search?q={urllib.parse.quote(q)}"
        li_kw = f"{company} {clean_city} " + ("Mechanical Engineer" if "Peer" in role else "Engineering Manager" if "Senior" in role else "Talent Acquisition")
        li_url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(li_kw)}"
        links[role] = (google_url, li_url)
    return links

def fetch_jobs():
    """Fetches recent jobs from Active Jobs DB (RapidAPI) using minimal quota."""
    url = "https://active-jobs-db.p.rapidapi.com/active-jobs-7d"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "active-jobs-db.p.rapidapi.com"
    }
    # 1 broad query per 4-hour run = 6 calls/day = ~180 calls/month (Well under 250 limit!)
    params = {
        "title_filter": '"Mechanical Engineer" OR "Design Engineer" OR "CAE Engineer" OR "FEA" OR "CFD" OR "R&D Engineer" OR "Product Design" OR "Mechatronics"',
        "location_filter": "India",
        "limit": "25"
    }
    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        return r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    except Exception as e:
        print(f"API Fetch Error: {e}")
        return []

def classify_and_tailor(company, title, location, description):
    """Uses Gemini Pro to pick the exact lane, fill the cover note, and spot JD gaps."""
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
    try:
        resp = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        return json.loads(resp.text)
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"lane": "consumer", "jd_hook": "mechanical design, simulation, and DFM", "specific_gaps": "Review core JD tools."}

def send_telegram_alert(text, resume_filename):
    """Sends the formatted job package and attaches the right PDF resume."""
    msg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(msg_url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })
    
    pdf_path = os.path.join("resumes", resume_filename)
    if os.path.exists(pdf_path):
        doc_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        with open(pdf_path, "rb") as f:
            requests.post(doc_url, data={"chat_id": TELEGRAM_CHAT_ID}, files={"document": f})

def main():
    seen_jobs = load_seen_jobs()
    jobs = fetch_jobs()
    
    for job in jobs:
        job_id = str(job.get("id") or job.get("url"))
        if not job_id or job_id in seen_jobs:
            continue
            
        title = job.get("title", "Mechanical Engineer")
        company = job.get("organization", "Unknown Company")
        location = str(job.get("locations_derived", ["India"]))
        url = job.get("url", "#")
        desc = job.get("description_text", "")
        
        # Location priority flag
        loc_lower = location.lower()
        is_primary = any(city in loc_lower for city in PRIMARY_LOCATIONS)
        loc_flag = "🟢 PRIMARY LOCATION" if is_primary else f"🟡 SECONDARY LOCATION ({location})"
        
        # Run AI analysis
        analysis = classify_and_tailor(company, title, location, desc)
        lane_key = analysis.get("lane", "consumer")
        if lane_key not in LANES:
            lane_key = "consumer"
        lane_info = LANES[lane_key]
        
        # Build Cover Note
        subject = lane_info["subject"].format(company=company)
        note = lane_info["note_template"].format(
            name="[Name]",
            company=company,
            title=title,
            jd_hook=analysis.get("jd_hook", "mechanical design and analysis")
        )
        
        # Build Networking URLs
        net_links = build_networking_links(company, location, lane_key)
        net_text = "\n".join([f"• <b>{role}:</b> <a href='{g_url}'>Google X-Ray</a> | <a href='{l_url}'>LinkedIn Search</a>" for role, (g_url, l_url) in net_links.items()])
        
        # Assemble Telegram Alert
        telegram_msg = (
            f"🎯 <b>{title} — {company}</b>\n"
            f"📍 {loc_flag}\n"
            f"🏷 <b>Lane:</b> {lane_info['name']} (<code>{lane_info['resume']}</code>)\n"
            f"🔗 <a href='{url}'>Click Here to Review & Apply</a>\n\n"
            f"👥 <b>Networking Links (No Login Needed):</b>\n{net_text}\n\n"
            f"✉️ <b>Tailored Outreach Draft:</b>\n"
            f"<b>Subject:</b> <code>{subject}</code>\n"
            f"<pre>{note}</pre>\n\n"
            f"⚠️ <b>JD-Specific Gaps:</b>\n{analysis.get('specific_gaps')}\n\n"
            f"📚 <b>Revise Before Interview:</b>\n{lane_info['revise']}"
        )
        
        send_telegram_alert(telegram_msg, lane_info["resume"])
        seen_jobs.add(job_id)
        
    save_seen_jobs(seen_jobs)

if __name__ == "__main__":
    main()