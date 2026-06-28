#!/usr/bin/env python3
"""
Generate icon assets from SVG data using Pillow only.
Produces: assets/icon.png, assets/icon.ico, assets/icon.icns
Run before PyInstaller.
"""

import os
import sys
import struct
import zlib
import io
from pathlib import Path

# ── Try to import Pillow ───────────────────────────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    print("Installing Pillow...")
    os.system(f"{sys.executable} -m pip install Pillow")
    from PIL import Image, ImageDraw, ImageFilter


ASSETS_DIR = Path(__file__).parent.parent / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


# ── Draw the icon programmatically (no SVG parser needed) ─────────────────────

def draw_icon(size: int) -> Image.Image:
    """Draw OmniLauncher-MC icon at given size, returns RGBA image."""
    scale = size / 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── Background rounded rect ──────────────────────────────────────────
    radius = int(80 * scale)
    bg_color_top = (108, 59, 245, 255)   # #6C3BF5
    bg_color_bot = (59, 130, 246, 255)   # #3B82F6

    # Gradient simulation: draw horizontal bands
    for y in range(size):
        t = y / size
        r = int(bg_color_top[0] * (1 - t) + bg_color_bot[0] * t)
        g = int(bg_color_top[1] * (1 - t) + bg_color_bot[1] * t)
        b = int(bg_color_top[2] * (1 - t) + bg_color_bot[2] * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # Mask to rounded rect
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    pad = int(32 * scale)
    mask_draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=radius,
        fill=255,
    )
    img.putalpha(mask)

    draw = ImageDraw.Draw(img)

    # ── Circle (O symbol) ────────────────────────────────────────────────
    cx, cy = size // 2, int(240 * scale)
    r_outer = int(100 * scale)
    r_inner = r_outer - int(28 * scale)
    stroke = int(28 * scale)

    # Draw filled circle then inner cutout
    draw.ellipse(
        [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
        fill=(255, 255, 255, 240),
    )
    draw.ellipse(
        [cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner],
        fill=None,
        outline=None,
    )

    # Re-draw circle as ring using stroke
    draw.ellipse(
        [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
        fill=None,
        outline=(255, 255, 255, 240),
        width=stroke,
    )

    # Redraw correct: filled white ring approach
    # Draw big white circle, then overlay gradient ellipse for the hole
    draw.ellipse(
        [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
        fill=(255, 255, 255, 220),
    )

    # Inner hole - redraw gradient
    hole_r = r_outer - stroke
    for hy in range(cy - hole_r, cy + hole_r):
        if 0 <= hy < size:
            t = hy / size
            rr = int(bg_color_top[0] * (1 - t) + bg_color_bot[0] * t)
            gg = int(bg_color_top[1] * (1 - t) + bg_color_bot[1] * t)
            bb = int(bg_color_top[2] * (1 - t) + bg_color_bot[2] * t)
            # chord width at this y
            dy = hy - cy
            if abs(dy) <= hole_r:
                chord = int((hole_r**2 - dy**2) ** 0.5)
                draw.line(
                    [(cx - chord, hy), (cx + chord, hy)],
                    fill=(rr, gg, bb, 255),
                )

    draw = ImageDraw.Draw(img)

    # ── Play triangle ─────────────────────────────────────────────────────
    # Points relative to center circle
    tx = int(20 * scale)   # nudge right for visual balance
    th = int(40 * scale)   # half-height
    tw = int(48 * scale)   # width
    pts = [
        (cx - int(14 * scale) + tx, cy - th),
        (cx - int(14 * scale) + tx + tw, cy),
        (cx - int(14 * scale) + tx, cy + th),
    ]
    draw.polygon(pts, fill=(255, 255, 255, 240))

    # ── "MC" text at bottom ───────────────────────────────────────────────
    text_y = int(360 * scale)
    font_size = int(64 * scale)

    # Draw MC as simple block letters (no font dependency)
    _draw_mc_text(draw, cx, text_y, font_size)

    return img


def _draw_mc_text(draw: ImageDraw.ImageDraw, cx: int, y: int, font_size: int):
    """Draw block 'MC' letters manually."""
    w = font_size
    h = font_size
    thickness = max(3, font_size // 6)
    gap = font_size // 4
    total_w = w * 2 + gap
    start_x = cx - total_w // 2

    # Draw M
    mx = start_x
    # Left vertical
    draw.rectangle([mx, y, mx + thickness, y + h], fill=(255, 255, 255, 230))
    # Right vertical
    draw.rectangle([mx + w - thickness, y, mx + w, y + h], fill=(255, 255, 255, 230))
    # Left diagonal down
    for i in range(h // 2):
        frac = i / (h // 2)
        draw.rectangle(
            [mx + thickness + int(frac * (w // 2 - thickness)),
             y + i,
             mx + thickness + int(frac * (w // 2 - thickness)) + thickness,
             y + i + thickness],
            fill=(255, 255, 255, 230),
        )
    # Right diagonal down
    for i in range(h // 2):
        frac = i / (h // 2)
        draw.rectangle(
            [mx + w - thickness - int(frac * (w // 2 - thickness)) - thickness,
             y + i,
             mx + w - thickness - int(frac * (w // 2 - thickness)),
             y + i + thickness],
            fill=(255, 255, 255, 230),
        )

    # Draw C
    cx2 = start_x + w + gap
    # Top bar
    draw.rectangle([cx2, y, cx2 + w, y + thickness], fill=(255, 255, 255, 230))
    # Bottom bar
    draw.rectangle([cx2, y + h - thickness, cx2 + w, y + h], fill=(255, 255, 255, 230))
    # Left vertical
    draw.rectangle([cx2, y, cx2 + thickness, y + h], fill=(255, 255, 255, 230))


# ── PNG generation ─────────────────────────────────────────────────────────────

def save_png(size: int = 512) -> Path:
    out = ASSETS_DIR / "icon.png"
    img = draw_icon(size)
    img.save(str(out), "PNG")
    print(f"  ✓ icon.png ({size}x{size})")
    return out


# ── ICO generation ─────────────────────────────────────────────────────────────

def save_ico() -> Path:
    out = ASSETS_DIR / "icon.ico"
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    for s in sizes:
        img = draw_icon(s).convert("RGBA")
        images.append(img)

    # Save with largest as base, PIL handles ICO format
    images[0].save(
        str(out),
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"  ✓ icon.ico ({', '.join(str(s) for s in sizes)}px)")
    return out


# ── ICNS generation ────────────────────────────────────────────────────────────

def save_icns() -> Path:
    """
    Build a minimal .icns file manually.
    ICNS format: magic + length + repeated (OSType + length + PNG data)
    """
    out = ASSETS_DIR / "icon.icns"

    # OSType codes and pixel sizes for ICNS
    icon_types = [
        (b"ic04",   16),
        (b"ic05",   32),
        (b"ic07",   128),
        (b"ic08",   256),
        (b"ic09",   512),
        (b"ic10",   1024),
    ]

    chunks = []
    for ostype, px in icon_types:
        img = draw_icon(min(px, 512))
        if px > 512:
            # Upscale 512 → 1024 for ic10
            img = img.resize((px, px), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_data = buf.getvalue()

        # Each icon resource: OSType (4 bytes) + length (4 bytes, includes header) + data
        chunk_len = 8 + len(png_data)
        chunks.append(ostype + struct.pack(">I", chunk_len) + png_data)

    body = b"".join(chunks)
    total_len = 8 + len(body)  # magic(4) + total_length(4) + body

    with open(str(out), "wb") as f:
        f.write(b"icns")
        f.write(struct.pack(">I", total_len))
        f.write(body)

    print(f"  ✓ icon.icns ({', '.join(str(s) for _, s in icon_types)}px)")
    return out


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("🎨 Generating OmniLauncher-MC icons...")
    save_png(512)
    save_ico()
    save_icns()
    print("✅ All icons generated in assets/")


if __name__ == "__main__":
    main()