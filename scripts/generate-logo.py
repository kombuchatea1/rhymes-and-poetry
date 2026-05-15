#!/usr/bin/env python3
"""
Generate the R&P brand mark — sage circle with cream italic "R&P" — and the
favicon family from a single source spec.

Outputs:
  public/images/brand/logo-1024.png     — high-res logo on transparent bg
  public/images/brand/logo-512.png      — half-res variant
  public/favicon.png                     — 32x32 PNG favicon (modern browsers)
  public/favicon-16.png                  — 16x16 PNG favicon
  public/favicon-180.png                 — 180x180 Apple touch icon
  public/favicon.ico                     — multi-resolution ICO (16/32/48)
  public/favicon.svg                     — hand-crafted vector (best quality)

Run:
  python3 scripts/generate-logo.py
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Brand colors (matches src/styles/global.css)
SAGE = (74, 103, 65, 255)
CREAM = (250, 249, 246, 255)

# System fallback for italic serif. Liberation Serif renders close to Playfair
# Display at small sizes; not pixel-identical at large sizes but close enough
# for icons. The site's HTML/CSS continues to use Playfair via Google Fonts.
ITALIC_SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PUBLIC = PROJECT_ROOT / "public"
BRAND_DIR = PUBLIC / "images" / "brand"
BRAND_DIR.mkdir(parents=True, exist_ok=True)


def render_mark(size: int, text: str = "R&P", text_scale: float = 0.42) -> Image.Image:
    """Render the sage circle with cream italic text, centered, on transparent."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Circle fills the canvas with a 2% margin for anti-alias breathing room
    margin = max(1, int(size * 0.02))
    draw.ellipse([margin, margin, size - margin, size - margin], fill=SAGE)

    # Find the font size that fits text_scale of the diameter
    target_height = int(size * text_scale)
    font_size = target_height
    font = ImageFont.truetype(ITALIC_SERIF, font_size)

    # Tighten until it actually fits horizontally too (R&P is wider than tall)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    max_width = int(size * 0.72)
    while text_width > max_width and font_size > 6:
        font_size -= 1
        font = ImageFont.truetype(ITALIC_SERIF, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

    text_height = bbox[3] - bbox[1]
    # Centering accounts for the bbox y-offset (Liberation Serif's italic
    # has descender padding)
    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]

    draw.text((x, y), text, font=font, fill=CREAM)
    return img


def main():
    # Master logo at 1024 — good for OG cards, share images, anything large
    logo_1024 = render_mark(1024)
    logo_1024.save(BRAND_DIR / "logo-1024.png", "PNG", optimize=True)
    print(f"  ✓ {(BRAND_DIR / 'logo-1024.png').relative_to(PROJECT_ROOT)}")

    # 512 mid-size
    logo_512 = render_mark(512)
    logo_512.save(BRAND_DIR / "logo-512.png", "PNG", optimize=True)
    print(f"  ✓ {(BRAND_DIR / 'logo-512.png').relative_to(PROJECT_ROOT)}")

    # 180x180 Apple touch icon (iOS home screen). Add a subtle bg so the
    # circle shows on light home screens too.
    apple = render_mark(180)
    apple.save(PUBLIC / "favicon-180.png", "PNG", optimize=True)
    print(f"  ✓ {(PUBLIC / 'favicon-180.png').relative_to(PROJECT_ROOT)}")

    # 32x32 PNG (modern browsers prefer this over ICO for tab icons)
    fav_32 = render_mark(32)
    fav_32.save(PUBLIC / "favicon.png", "PNG", optimize=True)
    print(f"  ✓ {(PUBLIC / 'favicon.png').relative_to(PROJECT_ROOT)}")

    # 16x16 PNG (older browsers / small-pixel cases)
    fav_16 = render_mark(16)
    fav_16.save(PUBLIC / "favicon-16.png", "PNG", optimize=True)
    print(f"  ✓ {(PUBLIC / 'favicon-16.png').relative_to(PROJECT_ROOT)}")

    # Multi-resolution ICO — older browsers and "Save to bookmarks" use this
    fav_48 = render_mark(48)
    ico_path = PUBLIC / "favicon.ico"
    fav_16.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"  ✓ {ico_path.relative_to(PROJECT_ROOT)}")

    # Hand-crafted SVG — vector, scales infinitely, no font embedding needed
    # because browsers fall back through the family stack at render time
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <circle cx="50" cy="50" r="49" fill="#4a6741"/>
  <text
    x="50" y="50"
    text-anchor="middle"
    dominant-baseline="central"
    font-family="'Playfair Display', 'Didot', Georgia, serif"
    font-style="italic"
    font-weight="400"
    font-size="40"
    letter-spacing="-1"
    fill="#faf9f6"
  >R&amp;P</text>
</svg>
"""
    (PUBLIC / "favicon.svg").write_text(svg)
    print(f"  ✓ {(PUBLIC / 'favicon.svg').relative_to(PROJECT_ROOT)}")

    print("\nDone.")


if __name__ == "__main__":
    main()
