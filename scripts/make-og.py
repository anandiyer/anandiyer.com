#!/usr/bin/env python3
"""Generate the 1200×630 Open Graph image for anandiyer.com.

Matches the site's editorial aesthetic: serif on off-white, generous whitespace,
small mono label. No external dependencies beyond Pillow (preinstalled on most
macOS dev envs).

Run: python3 scripts/make-og.py
Output: images/og.png
"""
from __future__ import annotations
import pathlib
from PIL import Image, ImageDraw, ImageFont

# Site tokens
BG = (251, 250, 247)    # #fbfaf7
INK = (26, 26, 26)      # #1a1a1a
MUTED = (107, 107, 102) # #6b6b66
ACCENT = (31, 58, 138)  # #1f3a8a

W, H = 1200, 630

# Pillow can't ship font files; rely on system Apple fonts.
# Charter and Iowan Old Style ship with macOS; Menlo for mono.
SERIF_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Charter.ttc",
    "/Library/Fonts/Charter.ttc",
    "/System/Library/Fonts/Supplemental/Iowan Old Style.ttc",
    "/System/Library/Fonts/Times.ttc",
    "/System/Library/Fonts/Georgia.ttf",
]
MONO_CANDIDATES = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Courier.ttc",
]


def load(paths, size):
    for p in paths:
        if pathlib.Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 80px left/right padding, generous vertical centering
    pad = 80

    label = load(MONO_CANDIDATES, 22)
    name = load(SERIF_CANDIDATES, 132)
    tag = load(SERIF_CANDIDATES, 38)
    domain = load(MONO_CANDIDATES, 22)

    # Top: small mono label
    d.text((pad, pad), "ANAND  IYER", font=label, fill=MUTED, spacing=4)

    # Center stack: big name + tagline
    name_y = 180
    d.text((pad, name_y), "Anand Iyer", font=name, fill=INK)

    tag_y = name_y + 170
    d.text(
        (pad, tag_y),
        "Investor and founder.",
        font=tag,
        fill=INK,
    )
    d.text(
        (pad, tag_y + 56),
        "Managing Partner at Canonical.",
        font=tag,
        fill=MUTED,
    )

    # Bottom right: domain in mono
    domain_text = "anandiyer.com"
    bbox = d.textbbox((0, 0), domain_text, font=domain)
    dw = bbox[2] - bbox[0]
    d.text((W - pad - dw, H - pad - 22), domain_text, font=domain, fill=ACCENT)

    # Thin top-left accent rule (very subtle)
    d.line([(pad, pad - 18), (pad + 64, pad - 18)], fill=ACCENT, width=2)

    out = pathlib.Path(__file__).resolve().parent.parent / "images" / "og.png"
    out.parent.mkdir(exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out}  ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
