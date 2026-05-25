#!/usr/bin/env python3
"""Generate the full favicon set from images/anandiyer.jpg.

Outputs:
  /favicon.ico                            (multi-res 16+32)
  /images/favicon-16x16.png
  /images/favicon-32x32.png
  /images/apple-touch-icon.png            (180×180, iOS home screen)
  /images/android-chrome-192x192.png
  /images/android-chrome-512x512.png

Source: 400×400 X profile photo. Upscaling 400→512 with Lanczos is fine for
a photo of this composition (face fills frame). No external deps beyond Pillow.
"""
from __future__ import annotations
import pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "images" / "anandiyer.jpg"


def main():
    src = Image.open(SRC).convert("RGB")
    print(f"source: {SRC.name} {src.size}")

    sizes = {
        16:  ROOT / "images" / "favicon-16x16.png",
        32:  ROOT / "images" / "favicon-32x32.png",
        180: ROOT / "images" / "apple-touch-icon.png",
        192: ROOT / "images" / "android-chrome-192x192.png",
        512: ROOT / "images" / "android-chrome-512x512.png",
    }
    for size, path in sizes.items():
        img = src.resize((size, size), Image.LANCZOS)
        img.save(path, "PNG", optimize=True)
        print(f"  {size}×{size}  → {path.relative_to(ROOT)}")

    # Multi-resolution ICO at repo root (legacy browsers ask for /favicon.ico).
    ico_path = ROOT / "favicon.ico"
    src.resize((64, 64), Image.LANCZOS).save(
        ico_path, "ICO", sizes=[(16, 16), (32, 32), (48, 48)]
    )
    print(f"  ico      → {ico_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
