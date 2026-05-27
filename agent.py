"""
Agent — scores jobs against your career vault using Groq LLaMA
"""

import json
import re
from groq import Groq

with open("career_vault.json") as f:
    VAULT = json.load(f)

SYSTEM_PROMPT = f"""You are the Lead Career Strategist for a Full Auto Job Agent.

CAREER VAULT (USE ONLY THESE FACTS — ZERO HALLUCINATION):
{json.dumps(VAULT, indent=2)}

SCORING WEIGHTS:
- 40% Technical/Hard Skills match
- 30% Role Seniority/Experience match
- 30% Industry Alignment

RULES:
1. NEVER invent skills or facts not in the Career Vault
2. If match score < 80, output ONLY decision SKIP with skip_reason
3. Map Vault language to JD language
4. Respond ONLY with valid JSON — no markdown, no extra text

OUTPUT FORMAT:
{{
  "decision": "APPLY" or "SKIP",
  "match_score": <0-100>,
  "score_breakdown": {{
    "technical_skills": <0-40>,
    "seniority_experience": <0-30>,
    "industry_alignment": <0-30>
  }},
  "skip_reason": "N/A if applying",
  "matched_keywords": ["kw1", "kw2"],
  "missing_keywords": ["kw1", "kw2"],
  "tailored_bullets": ["bullet 1", "bullet 2", "bullet 3", "bullet 4", "bullet 5"],
  "resume_summary": "2-sentence summary tailored to this job",
  "cover_letter": "150 word cover letter — top 3 reasons for fit",
  "screening_answers": {{
    "Tell me about yourself": "2-3 sentences",
    "Why do you want this role": "2-3 sentences",
    "What is your greatest strength": "2-3 sentences relevant to JD",
    "Are you authorized to work in the US": "Yes, authorized to work in the US",
    "When can you start": "Immediately",
    "Years of AI/ML experience": "2 years building production AI systems"
  }},
  "sheet_log": "One sentence log e.g. Applied: 88% — Strong alignment with X"
}}"""

def score_job(job_text: str, groq_api_key: str) -> dict:
    client = Groq(api_key=groq_api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Evaluate this job:\n\n{job_text[:2500]}"}
        ],
        max_tokens=2000
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$",    "", raw)
    return json.loads(raw)
