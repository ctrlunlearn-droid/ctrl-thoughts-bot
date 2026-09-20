"""Slides ko 1080x1350 (4:5) JPEG images mein render karta hai (HTML/CSS + Playwright).

Design idea: brand "ctrl_thoughts_" = keyboard ki Ctrl key. Cover par ek shortcut
[Ctrl] + [Paisa/Body/Mindset] dikhta hai, baaki slides shaant rehti hain.
Slides dark aur light ke beech alternate hoti hain, aakhri CTA slide accent color par.
"""
import html
from pathlib import Path

from playwright.sync_api import sync_playwright

BRAND = "ctrl_thoughts_"
W, H = 1080, 1350

# accent: slide ke fill/underline ke liye. niche ke hisaab se badalta hai.
ACCENTS = {
    "finance": "#3DDC97",
    "fitness": "#FF7A59",
    "motivation": "#9A8CFF",
}
KEY_WORD = {"finance": "Paisa", "fitness": "Body", "motivation": "Mindset"}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=DM+Sans:wght@400;500;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:%(W)dpx;height:%(H)dpx}
body{font-family:'DM Sans','Segoe UI',Arial,sans-serif}
.slide{width:%(W)dpx;height:%(H)dpx;padding:88px 84px 80px;display:flex;flex-direction:column;
  background:var(--bg);color:var(--fg)}
.theme-dark{--bg:#1A1C25;--fg:#F2F1F7;--muted:#B3B5C4;--keybg:#2B2E3B;--keyfg:#F2F1F7;--keyedge:#0E0F15}
.theme-light{--bg:#ECE9F3;--fg:#1A1C25;--muted:#4B4E5C;--keybg:#FFFFFF;--keyfg:#1A1C25;--keyedge:#B9B5C8}
.theme-accent{--bg:var(--accent);--fg:#15161D;--muted:#23252F;--keybg:#15161D;--keyfg:#FFFFFF;--keyedge:#000000}
header{display:flex;justify-content:space-between;align-items:center;height:64px}
.brand{font-family:'Space Grotesk',sans-serif;font-weight:500;font-size:32px;letter-spacing:.01em;color:var(--muted)}
.key{display:inline-flex;align-items:center;justify-content:center;min-width:64px;height:64px;padding:0 22px;
  border-radius:14px;background:var(--keybg);color:var(--keyfg);font-family:'Space Grotesk',sans-serif;
  font-weight:700;font-size:28px;box-shadow:0 6px 0 var(--keyedge)}
.key.big{min-width:150px;height:150px;padding:0 40px;border-radius:30px;font-size:58px;box-shadow:0 12px 0 var(--keyedge)}
.key.accent{background:var(--accent);color:#15161D}
main{flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column;justify-content:center;padding:40px 0}
h1,h2{font-family:'Space Grotesk',sans-serif;font-weight:700;letter-spacing:-.025em;line-height:1.05}
h1{font-size:118px}
h2{font-size:104px}
.bar{width:120px;height:14px;border-radius:7px;background:var(--accent);margin:44px 0 40px}
.sub,.body{color:var(--muted);line-height:1.38;font-weight:400}
.sub{font-size:48px;max-width:900px}
.body{font-size:56px;max-width:912px}
.combo{display:flex;align-items:center;gap:26px;margin-bottom:70px}
.plus{font-family:'Space Grotesk',sans-serif;font-size:52px;font-weight:500;color:var(--muted)}
footer{height:64px;display:flex;align-items:center;justify-content:flex-end;gap:18px;
  font-size:30px;color:var(--muted)}
.handle{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:64px;letter-spacing:-.02em;margin-top:44px}
"""

JS = """
function fit(){
  const m=document.getElementById('main');
  const els=[...document.querySelectorAll('[data-fit]')];
  let g=0;
  while(m.scrollHeight>m.clientHeight+1 && g<80){
    els.forEach(e=>{const s=parseFloat(getComputedStyle(e).fontSize);e.style.fontSize=(s-2)+'px';});
    g++;
  }
}
"""


def _e(text: str) -> str:
    return html.escape(str(text or "").strip())


def _theme_for(index: int, total: int, slide_type: str) -> str:
    if slide_type == "cta":
        return "accent"
    if slide_type == "cover":
        return "dark"
    # content slides: light, dark, light, dark ...
    return "light" if index % 2 == 0 else "dark"


def _main_html(slide: dict, niche: str) -> str:
    t = slide.get("type")
    if t == "cover":
        return f"""
        <div class="combo"><span class="key big">Ctrl</span><span class="plus">+</span>
        <span class="key big accent">{_e(KEY_WORD[niche])}</span></div>
        <h1 data-fit>{_e(slide['title'])}</h1>
        <div class="bar"></div>
        <p class="sub" data-fit>{_e(slide.get('subtitle', ''))}</p>"""
    if t == "cta":
        return f"""
        <h2 data-fit>{_e(slide['title'])}</h2>
        <div class="bar" style="background:#15161D"></div>
        <p class="body" data-fit>{_e(slide.get('body', ''))}</p>
        <p class="handle">@{BRAND}</p>"""
    return f"""
        <h2 data-fit>{_e(slide['title'])}</h2>
        <div class="bar"></div>
        <p class="body" data-fit>{_e(slide.get('body', ''))}</p>"""


def build_html(slide: dict, index: int, total: int, niche: str) -> str:
    theme = _theme_for(index, total, slide.get("type"))
    accent = ACCENTS[niche]
    footer = ""
    if slide.get("type") == "cover":
        footer = '<footer>swipe karo <span class="key">→</span></footer>'
    else:
        footer = "<footer></footer>"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS % {'W': W, 'H': H}}</style></head>
<body><div class="slide theme-{theme}" style="--accent:{accent}">
<header><div class="brand">{BRAND}</div><div class="key">{index}/{total}</div></header>
<main id="main">{_main_html(slide, niche)}</main>
{footer}
</div><script>{JS}</script></body></html>"""


def render_slides(slides: list[dict], niche: str, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    total = len(slides)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        for i, slide in enumerate(slides, start=1):
            page.set_content(build_html(slide, i, total, niche))
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
                page.evaluate("document.fonts.ready")
            except Exception:
                pass  # font load fail ho to fallback fonts chalenge
            page.evaluate("fit()")
            path = out_dir / f"slide_{i}.jpg"
            page.screenshot(path=str(path), type="jpeg", quality=92)
            paths.append(path)
        browser.close()
    return paths
