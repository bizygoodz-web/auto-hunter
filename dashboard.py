"""
Render Dashboard — monitors all applications from the local agent
Deploy this to Render. Local agent writes to applications.json,
dashboard reads it and shows live stats.
"""

import streamlit as st
import json
import os
from datetime import datetime, date

st.set_page_config(page_title="Job Hunt Dashboard", page_icon="🎯", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background: #0a0a0f; color: #e8e8f0; }
.card {
    background: #12121a; border: 1px solid #2a2a3f;
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.6rem;
}
.card-apply { border-left: 3px solid #00e676; }
.card-skip  { border-left: 3px solid #333; }
.card-done  { border-left: 3px solid #6c63ff; }
.metric-box {
    background: linear-gradient(135deg,#12121a,#1a1a28);
    border: 1px solid #2a2a3f; border-radius: 12px;
    padding: 1.2rem; text-align: center; position: relative; overflow: hidden;
}
.metric-box::before { content:''; position:absolute; top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,#6c63ff,#ff6584); }
.metric-val { font-size: 2.2rem; font-weight: 800; color: #6c63ff; }
.metric-lbl { font-size: 0.7rem; color: #888; text-transform: uppercase; letter-spacing: 0.1em; }
.tag { background:#1e1e2e; border:1px solid #3a3a5c; border-radius:4px;
    padding:2px 7px; font-size:0.72rem; color:#aaa; margin:2px;
    display:inline-block; font-family:'JetBrains Mono',monospace; }
</style>
""", unsafe_allow_html=True)

LOG_FILES = ["applications.json", "applications_log.json"]

def load_all_applications():
    all_apps = []
    seen_urls = set()
    for fname in LOG_FILES:
        if os.path.exists(fname):
            try:
                with open(fname) as f:
                    data = json.load(f)
                for item in data:
                    url = item.get("url","")
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_apps.append(item)
            except: pass
    all_apps.sort(key=lambda x: x.get("timestamp",""), reverse=True)
    return all_apps

# ── Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:1.5rem 0 0.5rem;">
  <h1 style="font-family:'Syne',sans-serif;font-weight:800;font-size:2rem;margin:0;
             background:linear-gradient(90deg,#6c63ff,#ff6584);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
    🎯 Job Hunt Dashboard
  </h1>
  <p style="color:#555;font-family:'JetBrains Mono',monospace;font-size:0.8rem;margin:0.2rem 0 0;">
    Tirumalarao Kilari · Live feed from local agent
  </p>
</div>
""", unsafe_allow_html=True)

if st.button("🔄 Refresh", type="secondary"):
    st.rerun()

apps = load_all_applications()

if not apps:
    st.info("No applications yet. Run `python main.py --dry-run` on your local machine to start.")
    st.stop()

# ── Stats ─────────────────────────────────────────────────────────────────
total     = len(apps)
matches   = [a for a in apps if a.get("decision") == "APPLY"]
applied   = [a for a in apps if a.get("status") == "applied"]
skipped   = [a for a in apps if a.get("decision") == "SKIP"]
today_str = date.today().isoformat()
today     = [a for a in apps if a.get("date") == today_str]
avg_score = int(sum(a.get("match_score",0) for a in apps) / max(len(apps),1))
top_score = max((a.get("match_score",0) for a in apps), default=0)

c1,c2,c3,c4,c5,c6 = st.columns(6)
for col, val, lbl, color in [
    (c1, total,         "Total Evaluated", "#6c63ff"),
    (c2, len(matches),  "Matches (80%+)",  "#00e676"),
    (c3, len(applied),  "Applied",         "#6c63ff"),
    (c4, len(skipped),  "Skipped",         "#ff5252"),
    (c5, f"{avg_score}%","Avg Score",      "#ffd740"),
    (c6, f"{top_score}%","Best Match",     "#00e676"),
]:
    col.markdown(f"""
    <div class="metric-box">
      <div class="metric-val" style="color:{color}">{val}</div>
      <div class="metric-lbl">{lbl}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["✅ Matches", "📋 All Applications", "📊 Stats"])

# ── Tab 1: Matches ────────────────────────────────────────────────────────
with tab1:
    st.subheader(f"✅ {len(matches)} Matches (80%+ gate)")
    if not matches:
        st.info("No matches yet — run the agent to find jobs.")
    for a in matches:
        score   = a.get("match_score", 0)
        status  = a.get("status", "")
        icon    = "✅" if status == "applied" else "🟡"
        source  = a.get("source", "")
        url     = a.get("url", "")

        with st.expander(f"{icon} {score}% — {a['title']} @ {a['company']}  [{source}]"):
            col_l, col_r = st.columns([3,1])
            with col_l:
                st.caption(f"📅 {a.get('timestamp','')[:19]}  ·  {source}  ·  Status: **{status}**")
                if url:
                    st.markdown(f"🔗 [Open Application]({url})")
                kw = a.get("matched_keywords", [])
                if kw:
                    st.markdown("**Matched:** " + " ".join(f'<span class="tag">{k}</span>' for k in kw[:8]), unsafe_allow_html=True)
                bullets = a.get("tailored_bullets", [])
                if bullets:
                    st.markdown("**Tailored bullets:**")
                    for b in bullets[:3]:
                        st.markdown(f"• {b}")
                cover = a.get("cover_letter", "")
                if cover:
                    with st.expander("Cover letter"):
                        st.text(cover)
                screening = a.get("screening_answers", {})
                if screening:
                    with st.expander("Screening answers"):
                        for q, ans in screening.items():
                            st.markdown(f"**{q}**")
                            st.code(ans, language=None)
            with col_r:
                bd = a.get("score_breakdown", {})
                st.metric("Technical",  f"{bd.get('technical_skills',0)}/40")
                st.metric("Seniority",  f"{bd.get('seniority_experience',0)}/30")
                st.metric("Industry",   f"{bd.get('industry_alignment',0)}/30")

# ── Tab 2: All Applications ───────────────────────────────────────────────
with tab2:
    st.subheader("📋 All Applications")
    f1, f2, f3 = st.columns(3)
    with f1: fd = st.selectbox("Decision", ["All","APPLY","SKIP"])
    with f2: fs = st.selectbox("Source",   ["All"] + list(set(a.get("source","") for a in apps if a.get("source"))))
    with f3: fst= st.selectbox("Status",   ["All","applied","ready_to_apply","skipped"])

    filtered = apps
    if fd  != "All": filtered = [a for a in filtered if a.get("decision") == fd]
    if fs  != "All": filtered = [a for a in filtered if a.get("source")   == fs]
    if fst != "All": filtered = [a for a in filtered if a.get("status")   == fst]

    st.caption(f"Showing {len(filtered)} of {len(apps)}")

    for a in filtered[:60]:
        decision = a.get("decision","SKIP")
        score    = a.get("match_score", 0)
        icon     = "✅" if decision=="APPLY" else "❌"
        st.markdown(f"""
        <div class="card {'card-apply' if decision=='APPLY' else 'card-skip'}">
          <b>{icon} {score}% — {a.get('title','')} @ {a.get('company','')}</b>
          <span style="color:#555;font-size:0.8rem;margin-left:1rem;">{a.get('source','')} · {a.get('date','')}</span>
          {'<br><span style="color:#888;font-size:0.85rem;">' + a.get('skip_reason','')[:80] + '</span>' if decision=='SKIP' else ''}
          {'<br><a href="' + a.get('url','') + '" target="_blank" style="color:#6c63ff;font-size:0.85rem;">Open →</a>' if a.get('url') else ''}
        </div>""", unsafe_allow_html=True)

    if st.button("⬇ Export JSON"):
        st.download_button("Download",
            data=json.dumps(apps, indent=2),
            file_name=f"applications_{today_str}.json",
            mime="application/json")

# ── Tab 3: Stats ──────────────────────────────────────────────────────────
with tab3:
    st.subheader("📊 Stats")

    # By source
    sources_count = {}
    for a in apps:
        s = a.get("source","Unknown")
        sources_count[s] = sources_count.get(s,0) + 1

    st.markdown("**Jobs by source:**")
    for src, cnt in sorted(sources_count.items(), key=lambda x: -x[1]):
        pct = int(cnt/max(total,1)*100)
        st.markdown(f"  `{src}` — {cnt} jobs ({pct}%)")

    # By day
    st.markdown("<br>**Applications by day:**", unsafe_allow_html=True)
    daily = {}
    for a in apps:
        d = a.get("date","")
        if d: daily[d] = daily.get(d,0) + 1
    for day, cnt in sorted(daily.items(), reverse=True)[:7]:
        st.markdown(f"  `{day}` — {cnt} jobs evaluated")

    # Top matches
    st.markdown("<br>**Top matches:**", unsafe_allow_html=True)
    top = sorted(matches, key=lambda x: x.get("match_score",0), reverse=True)[:5]
    for a in top:
        st.markdown(f"  ✅ **{a['match_score']}%** — {a['title']} @ {a['company']} [{a.get('source','')}]")

st.markdown("---")
st.caption("Full Auto Job Hunter · Local agent + Render dashboard · Tirumalarao Kilari")
