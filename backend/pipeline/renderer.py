import logging
import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Slide dimensions (Instagram portrait carousel)
SLIDE_WIDTH = 1080
SLIDE_HEIGHT = 1350

# Colour palette
BG_COLOR = "#FFFFFF"
ACCENT_COLOR = "#4F46E5"       # Indigo
TITLE_COLOR = "#111827"        # Near-black
BODY_COLOR = "#374151"         # Dark grey
SLIDE_NUM_COLOR = "#9CA3AF"    # Light grey
DIVIDER_COLOR = "#E5E7EB"      # Very light grey

# Layout constants (px)
PADDING = 80
ACCENT_BAR_HEIGHT = 16
TITLE_Y_START = 340
DIVIDER_Y_OFFSET = 60          # Below title baseline
BODY_Y_OFFSET = 100            # Below divider
SLIDE_NUM_MARGIN = 40

# Font size targets
TITLE_FONT_SIZE = 72
BODY_FONT_SIZE = 48
SMALL_FONT_SIZE = 36


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try common font paths; fall back to PIL built-in default."""
    candidates = []

    if bold:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/Arial Bold.ttf",
        ]
    else:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/Arial.ttf",
        ]

    # Also check for a bundled font in the backend/fonts/ directory
    backend_dir = Path(__file__).resolve().parent.parent
    local_candidates = [
        backend_dir / "fonts" / ("bold.ttf" if bold else "regular.ttf"),
    ]
    all_candidates = [str(p) for p in local_candidates] + candidates

    for path in all_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    logger.warning("No TrueType font found; falling back to PIL default (low quality).")
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines if lines else [text]


def _render_slide(slide: dict, output_path: str, total_slides: int) -> None:
    """Render a single slide image to disk."""
    img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # ── Accent bar (top) ───────────────────────────────────────────
    draw.rectangle([(0, 0), (SLIDE_WIDTH, ACCENT_BAR_HEIGHT)], fill=ACCENT_COLOR)

    # ── Slide number (top-right) ────────────────────────────────────
    small_font = _load_font(SMALL_FONT_SIZE)
    slide_num_text = f"{slide['index']} / {total_slides}"
    draw.text(
        (SLIDE_WIDTH - PADDING, SLIDE_NUM_MARGIN),
        slide_num_text,
        font=small_font,
        fill=SLIDE_NUM_COLOR,
        anchor="rt",
    )

    # ── Accent dot (left of slide number area) ──────────────────────
    dot_radius = 8
    dot_x = PADDING + dot_radius
    dot_y = SLIDE_NUM_MARGIN + (small_font.size // 2 if hasattr(small_font, "size") else 18)
    draw.ellipse(
        [(dot_x - dot_radius, dot_y - dot_radius), (dot_x + dot_radius, dot_y + dot_radius)],
        fill=ACCENT_COLOR,
    )

    # ── Title ───────────────────────────────────────────────────────
    title_font = _load_font(TITLE_FONT_SIZE, bold=True)
    max_text_width = SLIDE_WIDTH - (PADDING * 2)
    title_lines = _wrap_text(slide["title"], title_font, max_text_width, draw)

    y = TITLE_Y_START
    for line in title_lines:
        draw.text((PADDING, y), line, font=title_font, fill=TITLE_COLOR)
        bbox = draw.textbbox((0, 0), line, font=title_font)
        y += bbox[3] - bbox[1] + 12  # line height + leading

    title_bottom = y

    # ── Divider ─────────────────────────────────────────────────────
    divider_y = title_bottom + DIVIDER_Y_OFFSET
    draw.rectangle(
        [(PADDING, divider_y), (PADDING + 80, divider_y + 4)],
        fill=ACCENT_COLOR,
    )
    draw.rectangle(
        [(PADDING + 88, divider_y), (SLIDE_WIDTH - PADDING, divider_y + 4)],
        fill=DIVIDER_COLOR,
    )

    # ── Body ─────────────────────────────────────────────────────────
    body_font = _load_font(BODY_FONT_SIZE)
    body_lines = _wrap_text(slide["body"], body_font, max_text_width, draw)

    y = divider_y + BODY_Y_OFFSET
    for line in body_lines:
        draw.text((PADDING, y), line, font=body_font, fill=BODY_COLOR)
        bbox = draw.textbbox((0, 0), line, font=body_font)
        y += bbox[3] - bbox[1] + 16

    # ── Bottom accent bar ────────────────────────────────────────────
    draw.rectangle(
        [(0, SLIDE_HEIGHT - ACCENT_BAR_HEIGHT), (SLIDE_WIDTH, SLIDE_HEIGHT)],
        fill=ACCENT_COLOR,
    )

    img.save(output_path, "PNG")
    logger.info("Saved slide to %s", output_path)


def render_slides(slides: list[dict], output_dir: str) -> list[str]:
    """
    Render all slides to PNG images and save them to output_dir.

    Args:
        slides: Validated slide list [{"index": int, "title": str, "body": str}, ...].
        output_dir: Directory path where images will be saved.

    Returns:
        List of absolute file paths to the saved PNG images, ordered by slide index.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    total_slides = len(slides)
    paths = []

    for slide in sorted(slides, key=lambda s: s["index"]):
        filename = f"slide_{slide['index']}.png"
        output_path = os.path.join(output_dir, filename)
        _render_slide(slide, output_path, total_slides)
        paths.append(output_path)

    return paths
