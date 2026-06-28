#!/usr/bin/env python3
"""
Generate icon assets programmatically using Pillow.
Produces: assets/icon.png, assets/icon.ico, assets/icon.icns
Run before PyInstaller.
"""

import os
import sys
import struct
import io
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Installing Pillow...")
    os.system(f"{sys.executable} -m pip install Pillow")
    from PIL import Image, ImageDraw


ASSETS_DIR = Path(__file__).parent.parent / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def draw_icon(size: int) -> Image.Image:
    """Draw OmniLauncher-MC icon at given size, returns RGBA image."""
    scale = size / 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bg_color_top = (108, 59, 245, 255)
    bg_color_bot = (59, 130, 246, 255)

    # Gradient background
    for y in range(size):
        t = y / max(size - 1, 1)
        r = int(bg_color_top[0] * (1 - t) + bg_color_bot[0] * t)
        g = int(bg_color_top[1] * (1 - t) + bg_color_bot[1] * t)
        b = int(bg_color_top[2] * (1 - t) + bg_color_bot[2] * t)
        draw.line([(0, y), (size - 1, y)], fill=(r, g, b, 255))

    # Mask to rounded rect
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    pad = int(32 * scale)
    radius = int(80 * scale)
    mask_draw.rounded_rectangle(
        [pad, pad, size - pad - 1, size - pad - 1],
        radius=radius,
        fill=255,
    )
    img.putalpha(mask)

    # Need fresh draw after putalpha
    draw = ImageDraw.Draw(img)

    # White ring (O symbol)
    cx, cy = size // 2, int(220 * scale)
    r_outer = int(90 * scale)
    stroke = int(22 * scale)
    r_inner = r_outer - stroke

    # Draw white filled circle
    draw.ellipse(
        [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
        fill=(255, 255, 255, 230),
    )

    # Cut out inner hole by redrawing gradient
    for hy in range(max(0, cy - r_inner), min(size, cy + r_inner + 1)):
        dy = hy - cy
        if abs(dy) <= r_inner:
            chord = int((r_inner ** 2 - dy ** 2) ** 0.5)
            x_start = max(0, cx - chord)
            x_end = min(size - 1, cx + chord)
            t = hy / max(size - 1, 1)
            rr = int(bg_color_top[0] * (1 - t) + bg_color_bot[0] * t)
            gg = int(bg_color_top[1] * (1 - t) + bg_color_bot[1] * t)
            bb = int(bg_color_top[2] * (1 - t) + bg_color_bot[2] * t)
            draw.line([(x_start, hy), (x_end, hy)], fill=(rr, gg, bb, 255))

    # Play triangle
    tri_cx = cx + int(4 * scale)
    tri_h = int(36 * scale)
    tri_w = int(40 * scale)
    pts = [
        (tri_cx - int(12 * scale), cy - tri_h),
        (tri_cx - int(12 * scale) + tri_w, cy),
        (tri_cx - int(12 * scale), cy + tri_h),
    ]
    draw.polygon(pts, fill=(255, 255, 255, 240))

    # MC text as simple block letters
    if size >= 64:
        _draw_mc_text(draw, size // 2, int(350 * scale), int(50 * scale))

    return img


def _draw_mc_text(draw: ImageDraw.ImageDraw, cx: int, y: int, font_size: int):
    """Draw block M and C letters."""
    thickness = max(2, font_size // 7)
    w = font_size
    h = font_size
    gap = font_size // 3
    total_w = w * 2 + gap
    mx = cx - total_w // 2

    white = (255, 255, 255, 220)

    # M - left bar
    draw.rectangle([mx, y, mx + thickness, y + h], fill=white)
    # M - right bar
    draw.rectangle([mx + w - thickness, y, mx + w, y + h], fill=white)
    # M - top bar
    draw.rectangle([mx, y, mx + w, y + thickness], fill=white)
    # M - center V (simplified as center bar going down half)
    center_x = mx + w // 2
    draw.rectangle(
        [center_x - thickness // 2, y, center_x + thickness // 2, y + h // 2],
        fill=white,
    )

    # C
    cx2 = mx + w + gap
    # C - top bar
    draw.rectangle([cx2, y, cx2 + w, y + thickness], fill=white)
    # C - bottom bar
    draw.rectangle([cx2, y + h - thickness, cx2 + w, y + h], fill=white)
    # C - left bar
    draw.rectangle([cx2, y, cx2 + thickness, y + h], fill=white)


def save_png(size: int = 512) -> Path:
    out = ASSETS_DIR / "icon.png"
    img = draw_icon(size)
    img.save(str(out), "PNG")
    print("  [OK] icon.png (%dx%d)" % (size, size))
    return out


def save_ico() -> Path:
    out = ASSETS_DIR / "icon.ico"
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    for s in sizes:
        images.append(draw_icon(s).convert("RGBA"))

    images[-1].save(
        str(out),
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1],
    )
    print("  [OK] icon.ico (%s)" % ", ".join(str(s) for s in sizes))
    return out


def save_icns() -> Path:
    out = ASSETS_DIR / "icon.icns"

    icon_types = [
        (b"icp4", 16),
        (b"icp5", 32),
        (b"icp6", 64),
        (b"ic07", 128),
        (b"ic08", 256),
        (b"ic09", 512),
        (b"ic10", 1024),
    ]

    chunks = []
    for ostype, px in icon_types:
        img = draw_icon(min(px, 512))
        if px > 512:
            img = img.resize((px, px), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_data = buf.getvalue()

        chunk_len = 8 + len(png_data)
        chunks.append(ostype + struct.pack(">I", chunk_len) + png_data)

    body = b"".join(chunks)
    total_len = 8 + len(body)

    with open(str(out), "wb") as f:
        f.write(b"icns")
        f.write(struct.pack(">I", total_len))
        f.write(body)

    print("  [OK] icon.icns (%s)" % ", ".join(str(s) for _, s in icon_types))
    return out


def main():
    print("Generating OmniLauncher-MC icons...")
    save_png(512)
    save_ico()
    save_icns()
    print("All icons generated in assets/")


if __name__ == "__main__":
    main()