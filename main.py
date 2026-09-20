"""ctrl_thoughts_ carousel bot.

Commands:
  python main.py dry-run   -> content + slides banata hai ./out mein, post nahi karta (local test)
  python main.py prepare   -> content + slides banata hai ./posts/<date> mein (GitHub Actions)
  python main.py publish   -> ./posts/<date> ki images Instagram par post karta hai
"""
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv  # optional, sirf local .env ke liye
    load_dotenv()
except ImportError:
    pass

from generate import NICHES, build_caption, generate_content
from render import render_slides

ROOT = Path(__file__).parent
HISTORY = ROOT / "history.json"
POSTS = ROOT / "posts"
NICHE_ORDER = ["finance", "fitness", "motivation"]  # roz rotate hota hai
TZ = ZoneInfo("Asia/Kolkata")


def today() -> datetime:
    return datetime.now(TZ)


def load_history() -> list[dict]:
    try:
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def pick_niche(now: datetime) -> str:
    forced = os.environ.get("NICHE", "").strip().lower()
    if forced in NICHES:
        return forced
    return NICHE_ORDER[now.date().toordinal() % len(NICHE_ORDER)]


def prepare(out_root: Path) -> Path:
    now = today()
    niche = pick_niche(now)
    history = load_history()
    past_topics = [h["topic"] for h in history if h.get("niche") == niche]
    print(f"[prepare] niche: {niche}")

    data = generate_content(niche, past_topics)
    caption = build_caption(niche, data)

    folder = out_root / now.strftime("%Y-%m-%d")
    if folder.exists():
        shutil.rmtree(folder)
    paths = render_slides(data["slides"], niche, folder)

    manifest = {
        "date": now.strftime("%Y-%m-%d"),
        "niche": niche,
        "topic": data.get("topic", ""),
        "caption": caption,
        "images": [p.name for p in paths],
    }
    (folder / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[prepare] topic: {manifest['topic']}")
    print(f"[prepare] {len(paths)} slides -> {folder}")
    print("\n--- CAPTION ---\n" + caption + "\n---------------")
    return folder


def publish() -> None:
    from publish import post_carousel

    folders = sorted(p for p in POSTS.glob("*") if (p / "manifest.json").exists())
    if not folders:
        sys.exit("posts/ mein koi prepared post nahi mila. Pehle `prepare` chalao.")
    folder = folders[-1]
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))

    repo = os.environ["GITHUB_REPOSITORY"]  # owner/repo, Actions khud set karta hai
    branch = os.environ.get("PUBLISH_BRANCH", "main")
    base = f"https://raw.githubusercontent.com/{repo}/{branch}/posts/{folder.name}"
    urls = [f"{base}/{name}" for name in manifest["images"]]

    media_id = post_carousel(urls, manifest["caption"])

    history = load_history()
    history.append(
        {
            "date": manifest["date"],
            "niche": manifest["niche"],
            "topic": manifest["topic"],
            "media_id": media_id,
        }
    )
    HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "dry-run":
        prepare(ROOT / "out")
    elif cmd == "prepare":
        prepare(POSTS)
    elif cmd == "publish":
        publish()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
