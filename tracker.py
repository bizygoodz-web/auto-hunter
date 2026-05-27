"""
Tracker — logs every job evaluation to applications.json + sends daily email digest
"""

import json
import os
import smtplib
import time
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

LOG_FILE = "applications.json"

def load_log() -> list:
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE) as f:
                return json.load(f)
        except:
            return []
    return []

def save_log(data: list):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_result(job: dict, result: dict, status: str = None):
    log = load_log()
    decision = result.get("decision", "SKIP")
    if status is None:
        status = "applied" if decision == "APPLY" else "skipped"

    entry = {
        "id":               str(int(time.time())),
        "timestamp":        datetime.now().isoformat(),
        "date":             date.today().isoformat(),
        "title":            job.get("title", "Unknown"),
        "company":          job.get("company", "Unknown"),
        "url":              job.get("url", ""),
        "source":           job.get("source", ""),
        "decision":         decision,
        "match_score":      result.get("match_score", 0),
        "score_breakdown":  result.get("score_breakdown", {}),
        "skip_reason":      result.get("skip_reason", ""),
        "matched_keywords": result.get("matched_keywords", []),
        "missing_keywords": result.get("missing_keywords", []),
        "tailored_bullets": result.get("tailored_bullets", []),
        "cover_letter":     result.get("cover_letter", ""),
        "resume_summary":   result.get("resume_summary", ""),
        "screening_answers":result.get("screening_answers", {}),
        "sheet_log":        result.get("sheet_log", ""),
        "status":           status
    }
    log.insert(0, entry)
    save_log(log)
    return entry

def print_summary():
    log = load_log()
    today = date.today().isoformat()
    today_log   = [j for j in log if j.get("date") == today]
    applies     = [j for j in today_log if j.get("decision") == "APPLY"]
    skips       = [j for j in today_log if j.get("decision") == "SKIP"]
    total_apps  = sum(1 for j in log if j.get("status") == "applied")

    print(f"\n{'='*54}")
    print(f"  📊 TRACKER SUMMARY")
    print(f"{'='*54}")
    print(f"  Today evaluated : {len(today_log)}")
    print(f"  Today matches   : {len(applies)}")
    print(f"  Today skipped   : {len(skips)}")
    print(f"  Total applied   : {total_apps}")
    print(f"  Total in log    : {len(log)}")
    print(f"{'='*54}\n")

    if applies:
        print("  ✅ TODAY'S MATCHES:")
        for j in applies:
            print(f"  • {j['match_score']}% — {j['title']} @ {j['company']}")
            print(f"    {j.get('url','')}")

def send_daily_digest():
    smtp_user = os.environ.get("SMTP_EMAIL", "")
    smtp_pass = os.environ.get("SMTP_APP_PASSWORD", "")
    to_email  = os.environ.get("DIGEST_TO", smtp_user)

    if not smtp_user or not smtp_pass:
        print("⚠ Email digest skipped — set SMTP_EMAIL and SMTP_APP_PASSWORD env vars")
        return

    log     = load_log()
    today   = date.today().isoformat()
    t_jobs  = [j for j in log if j.get("date") == today]
    applies = [j for j in t_jobs if j.get("decision") == "APPLY"]
    skips   = [j for j in t_jobs if j.get("decision") == "SKIP"]

    html = f"""
<html><body style="font-family:Arial,sans-serif;background:#0a0a0f;color:#e8e8f0;padding:2rem;">
<h2 style="color:#6c63ff;">🎯 Job Agent — Daily Digest</h2>
<p style="color:#aaa;">{today} · {len(t_jobs)} evaluated · {len(applies)} matches</p>
<hr style="border-color:#2a2a3f;">
<h3 style="color:#00e676;">✅ Matches ({len(applies)})</h3>
{''.join(f"""
<div style="background:#12121a;border-left:3px solid #00e676;border-radius:8px;padding:1rem;margin-bottom:1rem;">
  <strong style="color:#fff;">{j['title']}</strong> @ {j['company']}<br>
  <span style="color:#6c63ff;font-weight:700;">{j['match_score']}% match</span>
  <span style="color:#aaa;margin-left:1rem;font-size:0.85em;">{j['source']}</span><br>
  <a href="{j['url']}" style="color:#6c63ff;">Open Application →</a><br>
  <em style="color:#888;font-size:0.85em;">{j.get('sheet_log','')}</em>
</div>""" for j in applies) if applies else "<p style='color:#888;'>No matches today.</p>"}
<h3 style="color:#ff5252;">❌ Skipped ({len(skips)})</h3>
{''.join(f"<p style='color:#888;font-size:0.85em;'>• {j['title']} @ {j['company']} — {j.get('skip_reason','')[:80]}</p>" for j in skips[:8])}
<hr style="border-color:#2a2a3f;">
<p style="color:#555;font-size:0.75em;">Full Auto Job Agent · Local Agent</p>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎯 Job Agent: {len(applies)} matches today ({today})"
    msg["From"]    = smtp_user
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"✅ Daily digest sent to {to_email}")
    except Exception as e:
        print(f"⚠ Email failed: {e}")
