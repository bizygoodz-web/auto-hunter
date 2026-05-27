"""
Full Auto Job Hunter — Main Controller
Runs on your computer. Scrapes jobs, scores them, opens browser to apply.
Usage:
    python main.py           # full run
    python main.py --dry-run # score only, no applying
    python main.py --once    # run once, no scheduler
"""

import os
import sys
import time
import json
import argparse
import schedule
from datetime import datetime

from job_scraper import scrape_all
from agent import score_job
from apply import open_and_fill
from tracker import log_result, send_daily_digest, load_log

# ── Config ────────────────────────────────────────────────────────────────────
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
SCAN_INTERVAL  = int(os.environ.get("SCAN_INTERVAL_HOURS", "6"))
MATCH_GATE     = 80  # minimum score to apply

KEYWORDS = [
    "AI Engineer",
    "Prompt Engineer",
    "LLM",
    "RAG",
    "Machine Learning Engineer",
    "Python Engineer",
    "NLP Engineer",
]

SOURCES = ["remoteok", "weworkremotely", "greenhouse", "lever", "ycombinator"]

def banner():
    print("""
╔══════════════════════════════════════════════════════╗
║        🎯 FULL AUTO JOB HUNTER — LOCAL AGENT         ║
║   Scrapes · Scores · Opens browser · Helps apply     ║
╚══════════════════════════════════════════════════════╝""")

def already_seen(url: str) -> bool:
    log = load_log()
    return any(j.get("url") == url for j in log if url)

def run_pipeline(dry_run: bool = False):
    print(f"\n{'='*54}")
    print(f"  RUN STARTED — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Mode: {'DRY RUN (no applying)' if dry_run else 'FULL (will open browser)'}")
    print(f"{'='*54}\n")

    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not set. Run:")
        print('   $env:GROQ_API_KEY="your_key_here"')
        return

    # ── 1. Scrape ────────────────────────────────────────────────────
    print("📡 Step 1 — Scraping job boards...")
    all_jobs = scrape_all(KEYWORDS, SOURCES)
    new_jobs = [j for j in all_jobs if not already_seen(j.get("url", ""))]
    print(f"   Found {len(all_jobs)} jobs total · {len(new_jobs)} new (not seen before)\n")

    if not new_jobs:
        print("   No new jobs found. Try again later or change keywords.")
        return

    # ── 2. Score ─────────────────────────────────────────────────────
    print(f"🤖 Step 2 — Scoring {len(new_jobs)} jobs with 80% gate...\n")
    matches = []

    for i, job in enumerate(new_jobs):
        title   = job.get("title", "Unknown")
        company = job.get("company", "Unknown")
        source  = job.get("source", "")
        print(f"  [{i+1}/{len(new_jobs)}] {title[:45]} @ {company[:25]}...")

        try:
            result = score_job(job.get("description", ""), GROQ_API_KEY)
            score  = result.get("match_score", 0)
            decision = result.get("decision", "SKIP")

            if decision == "APPLY":
                print(f"        ✅ {score}% — APPLY")
                matches.append({"job": job, "result": result})
            else:
                print(f"        ❌ {score}% — SKIP · {result.get('skip_reason','')[:60]}")

            log_result(job, result)
            time.sleep(2.5)  # 2.5 sec between requests — stays under rate limit

        except Exception as e:
            err = str(e)
            if "429" in err:
                print(f"        ⏳ Rate limited — waiting 30 seconds...")
                time.sleep(30)
                # Retry once
                try:
                    result = score_job(job.get("description", ""), GROQ_API_KEY)
                    score  = result.get("match_score", 0)
                    decision = result.get("decision", "SKIP")
                    if decision == "APPLY":
                        print(f"        ✅ {score}% — APPLY (retry)")
                        matches.append({"job": job, "result": result})
                    else:
                        print(f"        ❌ {score}% — SKIP (retry)")
                    log_result(job, result)
                    time.sleep(2.5)
                except Exception as e2:
                    print(f"        ⚠ Retry failed: {str(e2)[:60]}")
            else:
                print(f"        ⚠ Error: {err[:70]}")

    print(f"\n{'='*54}")
    print(f"  SCORING DONE — {len(matches)} matches out of {len(new_jobs)} jobs")
    print(f"{'='*54}\n")

    if not matches:
        print("No matches above 80% gate this run.")
        return

    # ── 3. Apply ─────────────────────────────────────────────────────
    if dry_run:
        print("DRY RUN — skipping apply phase. Matches found:")
        for m in matches:
            j = m["job"]
            r = m["result"]
            print(f"  ✅ {r['match_score']}% — {j['title']} @ {j['company']}")
            print(f"     {j.get('url','')}")
        print("\nRun without --dry-run to open browser and apply.")
        return

    print(f"🖥  Step 3 — Opening browser for {len(matches)} matches...\n")
    applied = 0

    for m in matches:
        job    = m["job"]
        result = m["result"]
        score  = result.get("match_score", 0)
        title  = job.get("title", "")
        company = job.get("company", "")

        print(f"\n{'─'*54}")
        print(f"  JOB: {title} @ {company}")
        print(f"  SCORE: {score}%")
        print(f"  URL: {job.get('url','')}")
        print(f"{'─'*54}")
        print(f"\n  COVER LETTER:\n  {result.get('cover_letter','')[:200]}...")
        print(f"\n  TAILORED BULLETS:")
        for b in result.get("tailored_bullets", [])[:3]:
            print(f"  • {b}")

        if job.get("url"):
            answer = input(f"\n  Open browser and fill form for this job? (y/n/q to quit): ").strip().lower()
            if answer == "q":
                print("  Quitting apply phase.")
                break
            if answer == "y":
                try:
                    open_and_fill(job, result)
                    log_result(job, result, status="applied")
                    applied += 1
                    print(f"  ✅ Form opened and pre-filled. Review → submit manually.")
                except Exception as e:
                    print(f"  ⚠ Browser error: {e}")
        else:
            print("  No URL — skipping browser.")

    print(f"\n{'='*54}")
    print(f"  DONE — Applied to {applied} of {len(matches)} matches")
    print(f"{'='*54}\n")

def main():
    banner()

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Score only, no browser")
    parser.add_argument("--once",    action="store_true", help="Run once, no schedule")
    args = parser.parse_args()

    if args.once or args.dry_run:
        run_pipeline(dry_run=args.dry_run)
        return

    # Scheduled mode
    print(f"⏰ Scheduler active — scanning every {SCAN_INTERVAL} hours")
    print(f"   First scan starting now...\n")

    run_pipeline(dry_run=False)

    schedule.every(SCAN_INTERVAL).hours.do(run_pipeline, dry_run=False)

    # Send daily digest at 8am
    schedule.every().day.at("08:00").do(send_daily_digest)

    print(f"\n✅ Scheduler running. Next scan in {SCAN_INTERVAL} hours.")
    print(f"   Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
