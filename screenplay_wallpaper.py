import datetime as dt
import subprocess
from pathlib import Path
import argparse
import re
import json

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont


# --- DISPLAY / STYLE CONFIG -------------------------------------------------

WIDTH, HEIGHT = 1920, 1080         # your monitor resolution
MARGIN_X = 140                     # left margin for text column
MARGIN_TOP_BOTTOM = 80             # top/bottom margin
FONT_SIZE = 28                     # tweak if you want bigger/smaller text
DEFAULT_WORDS_PER_PAGE = 900       # approx words per wallpaper

# base directory = folder where this script lives
SCRIPT_DIR = Path(__file__).resolve().parent


# --- HELPERS ----------------------------------------------------------------

def slugify(text: str) -> str:
    """Turn 'The_Godfather.html' or 'Pulp Fiction' into 'the_godfather', 'pulp_fiction'."""
    text = text.strip().lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_') or "script"


def download_and_store_script(script_url: str, slug: str) -> str:
    """Download screenplay HTML, extract text, normalise spaces, save as <slug>.txt."""
    print(f"Downloading screenplay from {script_url}...")
    resp = requests.get(script_url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    pre = soup.find("pre")
    text = pre.get_text() if pre else soup.get_text()

    # --- NORMALISE WEIRD SPACES / CONTROL CHARS ----------------------------
    # Convert non-breaking spaces and similar to normal spaces
    text = (
        text.replace("\u00a0", " ")  # NBSP
            .replace("\u2007", " ")  # figure space
            .replace("\u202f", " ")  # narrow NBSP
    )
    # Convert tabs (used in The Godfather) into normal indentation
    text = text.replace("\t", "    ")

    # Preserve line structure; just strip trailing whitespace
    # and remove any invisible control chars at the very start of the line
    lines = []
    for line in text.splitlines():
        # drop BOM or stray control chars at line start
        line = re.sub(r"^[\ufeff\u200b\u200c\u200d]+", "", line)
        lines.append(line.rstrip("\r\n"))

    cleaned = "\n".join(lines)
    # -----------------------------------------------------------------------

    script_txt = SCRIPT_DIR / f"{slug}.txt"
    script_txt.write_text(cleaned, encoding="utf-8")
    return cleaned


def load_script_text(script_url: str, slug: str) -> str:
    """Load cached <slug>.txt if present, otherwise download and cache it."""
    script_txt = SCRIPT_DIR / f"{slug}.txt"
    if script_txt.exists():
        print(f"Using cached script: {script_txt}")
        return script_txt.read_text(encoding="utf-8")
    else:
        return download_and_store_script(script_url, slug)


def chunk_into_pages_by_words_and_lines(text: str, words_per_page: int):
    """
    Walk line by line, counting words, and cut pages only on line boundaries.
    This keeps screenplay formatting intact (no re-wrapping).
    """
    lines = text.splitlines()
    pages = []

    current_lines = []
    current_word_count = 0

    for line in lines:
        words_in_line = len(line.strip().split()) if line.strip() else 0

        if current_word_count + words_in_line > words_per_page and current_lines:
            pages.append("\n".join(current_lines))
            current_lines = []
            current_word_count = 0

        current_lines.append(line)
        current_word_count += words_in_line

    if current_lines:
        pages.append("\n".join(current_lines))

    return pages


def get_font():
    """Try some monospace / typewriter-ish fonts available on macOS."""
    candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.dfont",
        "/Library/Fonts/Courier New.ttf",
    ]
    for path in candidates:
        p = Path(path)
        if p.exists():
            return ImageFont.truetype(str(p), FONT_SIZE)

    return ImageFont.load_default()


def render_page_to_image(text: str, out_path: Path, font):
    """
    Render a single page into a 1920x1080 image with
    black background and screenplay-yellow text.
    """

    BG_COLOR = (0, 0, 0)                    # Black
    TEXT_COLOR = (232, 217, 168)            # #E8D9A8

    # Create base image
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    lines = text.split("\n")

    # line height
    bbox = font.getbbox("A")
    line_height = (bbox[3] - bbox[1]) + 8

    max_lines_fit = (HEIGHT - 2 * MARGIN_TOP_BOTTOM) // line_height
    visible_lines = lines[:max_lines_fit]

    total_height = len(visible_lines) * line_height
    y = max(MARGIN_TOP_BOTTOM, (HEIGHT - total_height) // 2)

    for line in visible_lines:
        x = MARGIN_X
        draw.text((x, y), line.rstrip(), font=font, fill=TEXT_COLOR)
        y += line_height

    img.save(out_path)


def ensure_wallpapers(script_url: str, slug: str, words_per_page: int):
    """
    Ensure wallpapers exist for this script.
    Returns a sorted list of wallpaper paths.
    """
    output_dir = SCRIPT_DIR / f"wallpapers_{slug}"
    output_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(output_dir.glob("page_*.png"))
    if existing:
        print(f"Found {len(existing)} existing wallpaper pages for {slug}.")
        return existing

    full_text = load_script_text(script_url, slug)
    pages = chunk_into_pages_by_words_and_lines(full_text, words_per_page)
    print(f"Split into {len(pages)} pages of ~{words_per_page} words each.")

    font = get_font()
    image_paths = []
    for idx, page_text in enumerate(pages, start=1):
        out_path = output_dir / f"page_{idx:03d}.png"
        print(f"Generating {out_path.name}...")
        render_page_to_image(page_text, out_path, font)
        image_paths.append(out_path)

    return image_paths


def get_or_create_start_date(slug: str) -> dt.date:
    """
    For each script (slug), remember the start date in <slug>_meta.json.
    First run for that script → start date = today.
    Later runs reuse the same date.
    """
    meta_path = SCRIPT_DIR / f"{slug}_meta.json"

    if meta_path.exists():
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        try:
            return dt.date.fromisoformat(data["start_date"])
        except Exception:
            pass  # fall through to reset

    today = dt.date.today()
    meta_path.write_text(
        json.dumps({"start_date": today.isoformat()}, indent=2),
        encoding="utf-8",
    )
    return today


def pick_page_for_date(image_paths, start_date: dt.date, today=None):
    """Given a list of pages and a start date, pick today's page index."""
    if today is None:
        today = dt.date.today()

    days_since = (today - start_date).days
    if days_since < 0:
        days_since = 0

    idx = days_since % len(image_paths)
    return image_paths[idx]


def set_wallpaper_for_all_displays(image_path: Path):
    """
    Use AppleScript to apply the same wallpaper to ALL desktops / ALL monitors.
    This version matches the simple style that was working for you earlier.
    """
    path_str = str(image_path)

    script = f'''
    tell application "System Events"
        repeat with d in desktops
            set picture of d to "{path_str}"
        end repeat
    end tell
    '''
    subprocess.run(["osascript", "-e", script], check=True)

def unify_wallpaper_spaces():
    # Force macOS to use one wallpaper across all displays
    subprocess.run([
        "defaults", "-currentHost", "write",
        "com.apple.spaces", "spans-displays", "-bool", "true"
    ])
    subprocess.run(["killall", "Dock"])


# --- MAIN -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate and set 'screenplay page' wallpapers."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Screenplay URL (HTML) from dailyscript.com "
             "(e.g. https://www.dailyscript.com/scripts/pulp_fiction.html)",
    )
    parser.add_argument(
        "--name",
        help="Optional short name/slug (e.g., pulp_fiction, godfather). "
             "If omitted, will be derived from the URL.",
    )
    parser.add_argument(
        "--words-per-page",
        type=int,
        default=DEFAULT_WORDS_PER_PAGE,
        help="Approximate number of words per wallpaper page (default: 500).",
    )

    args = parser.parse_args()
    url = args.url

    if args.name:
        slug = slugify(args.name)
    else:
        last_part = url.rstrip("/").split("/")[-1]
        slug = slugify(last_part.rsplit(".", 1)[0])

    print(f"Using slug: {slug}")

    image_paths = ensure_wallpapers(url, slug, args.words_per_page)
    start_date = get_or_create_start_date(slug)
    today_page = pick_page_for_date(image_paths, start_date)

    print(f"Today's page for {slug}: {today_page.name}")

    unify_wallpaper_spaces()
    set_wallpaper_for_all_displays(today_page)
    unify_wallpaper_spaces()
    print("Wallpaper updated.")


if __name__ == "__main__":
    main()
