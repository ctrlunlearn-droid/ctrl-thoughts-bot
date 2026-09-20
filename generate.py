"""Gemini se carousel ka content (slides + caption) banata hai."""
import json
import os
import random
import time

from google import genai
from google.genai import types

BRAND = "ctrl_thoughts_"

NICHES = {
    "finance": {
        "label": "Finance",
        "brief": (
            "Personal finance for Indian young adults (18-35): saving, budgeting, SIP basics, "
            "emergency fund, credit card/loan traps, scams se bachna, paisa ki habits. "
            "Amounts ₹ mein likho. Kisi specific stock/coin ki salah mat do aur guaranteed "
            "returns ka wada mat karo."
        ),
        "disclaimer": "Sirf educational purpose ke liye hai, financial advice nahi hai.",
    },
    "fitness": {
        "label": "Fitness",
        "brief": (
            "Beginner-friendly fitness for Indians: simple workouts, gym-free exercises, "
            "protein aur Indian diet, sleep, recovery, consistency habits, common myths. "
            "Extreme diet ya unsafe claims mat karo."
        ),
        "disclaimer": "Koi bhi naya workout ya diet shuru karne se pehle doctor/expert se poochho.",
    },
    "motivation": {
        "label": "Motivation",
        "brief": (
            "Mindset, discipline, habits, focus, overthinking, self-growth. Generic "
            "'never give up' quotes nahi, practical aur relatable baatein jo padhne wale "
            "ko aaj hi kuch karne ko dein."
        ),
        "disclaimer": "",
    },
}


def _prompt(niche: str, n_slides: int, past_topics: list[str]) -> str:
    cfg = NICHES[niche]
    avoid = "\n".join(f"- {t}" for t in past_topics[-30:]) or "- (koi nahi)"
    return f"""Tu Instagram page "{BRAND}" ka content writer hai. Ek carousel post ka content bana.

NICHE: {cfg['label']}
FOCUS: {cfg['brief']}

LANGUAGE: Hinglish (Hindi Roman script mein + English words ka natural mix), jaise dost baat karta hai.
Devanagari script bilkul use mat karna. Tone: seedha, relatable, thoda punchy.

TOTAL SLIDES: exactly {n_slides}
- Slide 1: type "cover". Ek strong hook. Title max 9 words, subtitle max 14 words.
- Slide 2 se {n_slides - 1} tak: type "content". Har slide mein ek hi idea. Title max 7 words, body max 30 words.
  Slides ek flow mein hon (problem -> samajh -> solution/steps). Concrete example ya number do jahan ho sake.
- Slide {n_slides}: type "cta". Title max 6 words (jaise save/share/follow ke liye), body max 15 words.

CAPTION: 3-5 chhoti lines. Pehli line hook ho. Aakhri line mein comment karne ka sawal ho. Max 600 characters.
HASHTAGS: 8 se 10 relevant hashtags, "#" ke saath, Hinglish/English mix.

In topics par pehle post ho chuka hai, inhe repeat mat kar:
{avoid}

Sirf valid JSON return kar, is exact format mein:
{{
  "topic": "post ka short topic (English ya Hinglish)",
  "slides": [
    {{"type": "cover", "title": "...", "subtitle": "..."}},
    {{"type": "content", "title": "...", "body": "..."}},
    {{"type": "cta", "title": "...", "body": "..."}}
  ],
  "caption": "...",
  "hashtags": ["#...", "#..."]
}}"""


def _validate(data: dict, n_slides: int) -> None:
    slides = data.get("slides")
    if not isinstance(slides, list) or len(slides) != n_slides:
        raise ValueError(f"slides count galat hai (chahiye {n_slides})")
    if slides[0].get("type") != "cover" or slides[-1].get("type") != "cta":
        raise ValueError("pehli slide cover aur aakhri cta honi chahiye")
    for s in slides:
        if not s.get("title"):
            raise ValueError("kisi slide ka title khaali hai")
    if not data.get("caption"):
        raise ValueError("caption khaali hai")


def generate_content(niche: str, past_topics: list[str]) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY set nahi hai")
   model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
    client = genai.Client(api_key=api_key)

    n_slides = random.choice([7, 8])
    last_err = None
    for attempt in range(1, 5):
        try:
            resp = client.models.generate_content(
                model=model,
                contents=_prompt(niche, n_slides, past_topics),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.9,
                ),
            )
            data = json.loads(resp.text)
            _validate(data, n_slides)
            return data
        except Exception as e:  # rate limit, bad JSON, validation - sab par retry
            last_err = e
            wait = 5 * attempt
            print(f"[generate] attempt {attempt} fail: {e}. {wait}s baad retry...")
            time.sleep(wait)
    raise RuntimeError(f"Content generate nahi ho paya: {last_err}")


def build_caption(niche: str, data: dict) -> str:
    parts = [data["caption"].strip()]
    parts.append(f"Follow karo @{BRAND} for daily {NICHES[niche]['label'].lower()} ideas.")
    disclaimer = NICHES[niche]["disclaimer"]
    if disclaimer:
        parts.append(disclaimer)
    tags = []
    for t in data.get("hashtags", [])[:10]:
        t = t.strip().replace(" ", "")
        tags.append(t if t.startswith("#") else f"#{t}")
    if tags:
        parts.append(" ".join(tags))
    return "\n\n".join(parts)[:2200]
