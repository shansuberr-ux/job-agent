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