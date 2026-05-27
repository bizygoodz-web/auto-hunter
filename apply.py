"""
Apply — opens Chrome with Playwright, pre-fills application forms.
You review and click Submit manually.
"""

import json
import time
from playwright.sync_api import sync_playwright

with open("career_vault.json") as f:
    VAULT = json.load(f)

P = VAULT["personal"]
PREF = VAULT["preferences"]

# All your info — pulled from career vault
FORM_DATA = {
    "first_name":       P["name"].split()[0],
    "last_name":        " ".join(P["name"].split()[1:]),
    "full_name":        P["name"],
    "email":            P["email"],
    "phone":            P["phone"],
    "location":         P["location"],
    "city":             "Pflugerville",
    "state":            "TX",
    "linkedin":         P["linkedin"],
    "github":           P["github"],
    "website":          P.get("website", ""),
    "work_auth":        "Yes",
    "visa_sponsorship": "No",
    "salary":           PREF["salary"],
    "start_date":       PREF["available"],
    "remote":           "Yes",
    "years_experience": PREF.get("years_experience", "2"),
}

# Common field name patterns on job applications
FIELD_PATTERNS = {
    "first":      FORM_DATA["first_name"],
    "last":       FORM_DATA["last_name"],
    "name":       FORM_DATA["full_name"],
    "email":      FORM_DATA["email"],
    "phone":      FORM_DATA["phone"],
    "mobile":     FORM_DATA["phone"],
    "location":   FORM_DATA["location"],
    "city":       FORM_DATA["city"],
    "linkedin":   FORM_DATA["linkedin"],
    "github":     FORM_DATA["github"],
    "website":    FORM_DATA["website"],
    "portfolio":  FORM_DATA["github"],
    "salary":     FORM_DATA["salary"],
    "start":      FORM_DATA["start_date"],
    "available":  FORM_DATA["start_date"],
}

def try_fill_field(page, selector, value):
    """Try to fill a field, silently skip if not found."""
    try:
        el = page.locator(selector).first
        if el.count() > 0:
            el.fill(str(value))
            return True
    except:
        pass
    return False

def fill_text_inputs(page):
    """Smart-fill all text inputs by matching name/placeholder/label."""
    filled = 0
    inputs = page.locator("input[type='text'], input[type='email'], input[type='tel'], input:not([type])").all()
    for inp in inputs:
        try:
            name        = (inp.get_attribute("name") or "").lower()
            placeholder = (inp.get_attribute("placeholder") or "").lower()
            aria_label  = (inp.get_attribute("aria-label") or "").lower()
            combined    = f"{name} {placeholder} {aria_label}"

            for pattern, value in FIELD_PATTERNS.items():
                if pattern in combined and value:
                    inp.fill(str(value))
                    filled += 1
                    break
        except:
            continue
    return filled

def fill_cover_letter(page, cover_letter: str):
    """Find cover letter / additional info textarea and fill it."""
    textareas = page.locator("textarea").all()
    for ta in textareas:
        try:
            name        = (ta.get_attribute("name") or "").lower()
            placeholder = (ta.get_attribute("placeholder") or "").lower()
            aria_label  = (ta.get_attribute("aria-label") or "").lower()
            combined    = f"{name} {placeholder} {aria_label}"
            if any(k in combined for k in ["cover", "letter", "message", "additional", "why", "motivation"]):
                ta.fill(cover_letter)
                print("   ✓ Cover letter filled")
                return True
        except:
            continue
    return False

def open_and_fill(job: dict, result: dict):
    """
    Opens the job application URL in a visible Chrome browser.
    Pre-fills as many fields as possible.
    Pauses for human review before submitting.
    """
    url          = job.get("url", "")
    cover_letter = result.get("cover_letter", "")
    title        = job.get("title", "")
    company      = job.get("company", "")

    if not url:
        print("   No URL — cannot open browser.")
        return

    print(f"\n   🌐 Opening: {url}")
    print(f"   Pre-filling form for: {title} @ {company}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        ctx     = browser.new_context()
        page    = ctx.new_page()

        # Go to the job page
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)

        # Try to find and click "Apply" button if on job listing page
        for apply_text in ["Apply Now", "Apply for this job", "Apply", "Apply for position"]:
            try:
                btn = page.get_by_role("link", name=apply_text).first
                if btn.count() > 0:
                    btn.click()
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(1.5)
                    print(f"   ✓ Clicked '{apply_text}' button")
                    break
            except:
                continue

        # Fill text fields
        filled_count = fill_text_inputs(page)
        print(f"   ✓ Filled {filled_count} text fields")

        # Fill cover letter
        fill_cover_letter(page, cover_letter)

        # Print all info to console so you can copy-paste manually
        print("\n" + "─"*50)
        print("  📋 COPY-PASTE READY — Your info:")
        print("─"*50)
        print(f"  Name:         {FORM_DATA['full_name']}")
        print(f"  Email:        {FORM_DATA['email']}")
        print(f"  Phone:        {FORM_DATA['phone']}")
        print(f"  Location:     {FORM_DATA['location']}")
        print(f"  LinkedIn:     {FORM_DATA['linkedin']}")
        print(f"  GitHub:       {FORM_DATA['github']}")
        print(f"  Work Auth:    Yes, authorized to work in the US")
        print(f"  Visa:         No sponsorship needed")
        print(f"  Start:        Immediately")
        print(f"  Salary:       {FORM_DATA['salary']}")
        print("─"*50)
        print("\n  SCREENING ANSWERS:")
        for q, a in result.get("screening_answers", {}).items():
            print(f"\n  Q: {q}")
            print(f"  A: {a}")
        print("─"*50)
        print(f"\n  COVER LETTER:\n  {cover_letter}")
        print("─"*50)

        print("\n  ✋ Browser is open. Review the form, fill any remaining fields.")
        print("  Press Enter here when you have submitted (or skipped)...")
        input()

        browser.close()
        print("   Browser closed.")
