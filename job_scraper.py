"""
Job Scraper — pulls live jobs from RemoteOK, WeWorkRemotely, Greenhouse, Lever, YCombinator
"""

import httpx
from bs4 import BeautifulSoup
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def scrape_remoteok(keywords):
    jobs = []
    try:
        r = httpx.get("https://remoteok.com/api", headers=HEADERS, timeout=15)
        data = r.json()
        kw = [k.lower() for k in keywords]
        for item in data:
            if not isinstance(item, dict) or "position" not in item: continue
            title = item.get("position", "")
            desc  = BeautifulSoup(item.get("description", ""), "html.parser").get_text()[:2000]
            tags  = " ".join(item.get("tags", []))
            if any(k in f"{title} {desc} {tags}".lower() for k in kw):
                jobs.append({
                    "title":   title,
                    "company": item.get("company", "Unknown"),
                    "url":     item.get("url", f"https://remoteok.com/remote-jobs/{item.get('id','')}"),
                    "description": f"{title} at {item.get('company','')}. {desc}",
                    "source":  "RemoteOK"
                })
        print(f"   RemoteOK: {len(jobs)} jobs")
    except Exception as e:
        print(f"   RemoteOK error: {e}")
    return jobs[:20]

def scrape_weworkremotely(keywords):
    jobs = []
    feeds = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    ]
    kw = [k.lower() for k in keywords]
    for feed_url in feeds:
        try:
            r = httpx.get(feed_url, headers=HEADERS, timeout=12)
            soup = BeautifulSoup(r.text, "xml")
            for item in soup.find_all("item")[:20]:
                title = item.find("title").get_text() if item.find("title") else ""
                desc  = BeautifulSoup(item.find("description").get_text() if item.find("description") else "", "html.parser").get_text()[:2000]
                link  = item.find("link").get_text() if item.find("link") else ""
                if any(k in f"{title} {desc}".lower() for k in kw):
                    jobs.append({
                        "title":       title.strip(),
                        "company":     "Unknown",
                        "url":         link,
                        "description": f"{title}\n\n{desc}",
                        "source":      "WeWorkRemotely"
                    })
        except Exception as e:
            print(f"   WWR feed error: {e}")
    count = len(jobs)
    print(f"   WeWorkRemotely: {count} jobs")
    return jobs[:20]

def scrape_greenhouse(keywords):
    jobs = []
    kw = [k.lower() for k in keywords]
    companies = [
        "anthropic", "scale-ai", "cohere", "mistral", "replicate",
        "together", "anyscale", "modal", "runway", "perplexity",
        "huggingface", "openai", "stability"
    ]
    for company in companies:
        try:
            r = httpx.get(
                f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true",
                timeout=8
            )
            if r.status_code != 200: continue
            for job in r.json().get("jobs", []):
                title   = job.get("title", "")
                content = BeautifulSoup(job.get("content", ""), "html.parser").get_text()[:2000]
                if any(k in f"{title} {content}".lower() for k in kw):
                    jobs.append({
                        "title":       title,
                        "company":     company.replace("-", " ").title(),
                        "url":         job.get("absolute_url", ""),
                        "description": f"{title}\n\n{content}",
                        "source":      "Greenhouse"
                    })
            time.sleep(0.3)
        except: continue
    print(f"   Greenhouse: {len(jobs)} jobs")
    return jobs[:20]

def scrape_lever(keywords):
    jobs = []
    kw = [k.lower() for k in keywords]
    companies = ["openai", "scale", "cohere", "weights-biases", "together-ai", "anyscale"]
    for company in companies:
        try:
            r = httpx.get(f"https://api.lever.co/v0/postings/{company}?mode=json", timeout=8)
            if r.status_code != 200: continue
            for job in r.json():
                title = job.get("text", "")
                desc  = BeautifulSoup(job.get("descriptionPlain", ""), "html.parser").get_text()[:2000]
                if any(k in f"{title} {desc}".lower() for k in kw):
                    jobs.append({
                        "title":       title,
                        "company":     company.replace("-", " ").title(),
                        "url":         job.get("hostedUrl", ""),
                        "description": f"{title}\n\n{desc}",
                        "source":      "Lever"
                    })
            time.sleep(0.3)
        except: continue
    print(f"   Lever: {len(jobs)} jobs")
    return jobs[:15]

def scrape_ycombinator(keywords):
    jobs = []
    kw = [k.lower() for k in keywords]
    try:
        search_r = httpx.get(
            "https://hn.algolia.com/api/v1/search?query=Ask+HN+Who+is+hiring&tags=story,author_whoishiring&hitsPerPage=1",
            timeout=10
        )
        hits = search_r.json().get("hits", [])
        if not hits: return jobs
        story_id = hits[0]["objectID"]
        story = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=10).json()
        for kid_id in story.get("kids", [])[:50]:
            try:
                c    = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{kid_id}.json", timeout=6).json()
                text = BeautifulSoup(c.get("text", ""), "html.parser").get_text()[:2000]
                if any(k in text.lower() for k in kw):
                    first_line = text.split("\n")[0][:80]
                    jobs.append({
                        "title":       "See description",
                        "company":     first_line,
                        "url":         f"https://news.ycombinator.com/item?id={kid_id}",
                        "description": text,
                        "source":      "YCombinator"
                    })
            except: continue
    except Exception as e:
        print(f"   YC error: {e}")
    print(f"   YCombinator: {len(jobs)} jobs")
    return jobs[:10]

def scrape_all(keywords, sources=None):
    if sources is None:
        sources = ["remoteok", "weworkremotely", "greenhouse", "lever", "ycombinator"]

    all_jobs = []
    print(f"   Keywords: {', '.join(keywords[:5])}")

    if "remoteok"       in sources: all_jobs.extend(scrape_remoteok(keywords))
    if "weworkremotely" in sources: all_jobs.extend(scrape_weworkremotely(keywords))
    if "greenhouse"     in sources: all_jobs.extend(scrape_greenhouse(keywords))
    if "lever"          in sources: all_jobs.extend(scrape_lever(keywords))
    if "ycombinator"    in sources: all_jobs.extend(scrape_ycombinator(keywords))

    # Deduplicate by URL
    seen = set()
    unique = []
    for j in all_jobs:
        key = j.get("url") or j.get("title", "")
        if key and key not in seen:
            seen.add(key)
            unique.append(j)

    return unique
