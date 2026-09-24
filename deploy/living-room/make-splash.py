#!/usr/bin/env python3
"""Generate the default 3840x2160 living-room background (Pillow required)."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

W, H = 3840, 2160
canvas = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(canvas)
for y in range(H):
    t = y / (H - 1)
    draw.line((0, y, W, y), fill=(int(9 + 5 * t), int(16 + 10 * t), int(29 + 17 * t)))

glow = Image.new("RGBA", (W, H))
g = ImageDraw.Draw(glow)
g.ellipse((1800, -900, 5200, 2500), fill=(33, 170, 213, 78))
g.ellipse((2380, -350, 4750, 1850), fill=(113, 79, 233, 72))
glow = glow.filter(ImageFilter.GaussianBlur(220))
canvas = Image.alpha_composite(canvas.convert("RGBA"), glow)

lines = Image.new("RGBA", (W, H))
line_draw = ImageDraw.Draw(lines)
for offset in range(7):
    box = (2240 + offset * 115, 170 + offset * 85,
           4500 + offset * 115, 1740 + offset * 85)
    line_draw.arc(box, 133, 314, fill=(124, 210, 235, max(14, 75 - offset * 9)), width=3)
canvas = Image.alpha_composite(canvas, lines)
canvas.convert("RGB").save(Path(__file__).with_name("splash.png"), optimize=True)
