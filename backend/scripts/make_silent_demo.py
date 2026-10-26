"""Render a silent demo MP4 using imageio-ffmpeg (bundled binary)."""

from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "media"
MEDIA.mkdir(exist_ok=True)

W, H = 1280, 720
FPS = 30


def font(size: int) -> ImageFont.ImageFont:
    for path in (
        "C:/Windows/Fonts/georgia.ttf",
        "C:/Windows/Fonts/seguisb.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def card(bg: tuple[int, int, int], lines: list[tuple[str, int, tuple[int, int, int]]]) -> Image.Image:
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)
    for i in range(0, W, 10):
        shade = 6 + int(10 * math.sin(i / 80))
        draw.line(
            [(i, 0), (i, H)],
            fill=(min(255, bg[0] + shade), min(255, bg[1] + shade), min(255, bg[2] + shade)),
        )
    y = 150
    for text, size, color in lines:
        f = font(size)
        bbox = draw.textbbox((0, 0), text, font=f)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, y), text, fill=color, font=f)
        y += size + 26
    return img


def metrics_card(ov: dict) -> Image.Image:
    m = ov["overall"]
    img = Image.new("RGB", (W, H), (232, 244, 241))
    draw = ImageDraw.Draw(img)
    draw.text((80, 60), "January 2026 accuracy", fill=(11, 28, 36), font=font(42))
    rows = [
        ("MAE", f"{m['maeMw']} MW"),
        ("RMSE", f"{m['rmseMw']} MW"),
        ("Bias", f"{m['biasMw']} MW"),
        ("MAPE", f"{m['mapePct']}%"),
        ("Residual band (P90)", f"+/- {m['residualBandMw']} MW"),
        ("Paired intervals", str(m["n"])),
    ]
    y = 160
    for label, val in rows:
        draw.text((100, y), label, fill=(42, 68, 80), font=font(28))
        draw.text((720, y), val, fill=(14, 63, 56), font=font(28))
        y += 70
    return img


def fetch_overview() -> dict:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/overview", timeout=10) as r:
        return json.loads(r.read().decode())


def main() -> None:
    slides: list[tuple[Image.Image, float]] = [
        (
            card(
                (11, 28, 36),
                [
                    ("Boreas", 96, (232, 244, 241)),
                    ("Day-ahead GB wind desk", 36, (212, 165, 116)),
                    ("Silent walkthrough for morning narration", 24, (158, 201, 188)),
                ],
            ),
            4.0,
        ),
        (
            card(
                (232, 244, 241),
                [
                    ("Part 1 - Client pitch", 48, (11, 28, 36)),
                    ("Decision-window forecast vs actual", 28, (30, 58, 76)),
                    ("Residual procurement band for thermal cover", 24, (26, 107, 92)),
                ],
            ),
            5.0,
        ),
    ]

    try:
        slides.append((metrics_card(fetch_overview()), 6.0))
    except Exception as exc:  # noqa: BLE001
        slides.append(
            (
                card(
                    (232, 244, 241),
                    [
                        ("Metrics card (API offline)", 36, (139, 46, 46)),
                        (str(exc)[:70], 18, (42, 68, 80)),
                    ],
                ),
                4.0,
            )
        )

    slides.extend(
        [
            (
                card(
                    (14, 63, 56),
                    [
                        ("Decision rule", 48, (232, 244, 241)),
                        ("Latest WINDFOR publishTime", 28, (212, 165, 116)),
                        ("<= 09:20 CET on D-1 (EPEX GB gate)", 28, (232, 244, 241)),
                    ],
                ),
                5.0,
            ),
            (
                card(
                    (30, 58, 76),
                    [
                        ("Part 2 - Tech KT", 48, (232, 244, 241)),
                        ("React + FastAPI + Docker + Elexon cache", 26, (158, 201, 188)),
                        ("See SPEAKER_SCRIPT.md for narration", 22, (212, 165, 116)),
                    ],
                ),
                5.0,
            ),
            (
                card(
                    (11, 28, 36),
                    [
                        ("docker compose up --build", 40, (232, 244, 241)),
                        ("localhost:8080", 36, (212, 165, 116)),
                        ("github.com/Priyansh-max/mqxvn-k7wp", 24, (158, 201, 188)),
                    ],
                ),
                4.0,
            ),
        ]
    )

    out = MEDIA / "boreas-demo-silent.mp4"
    writer = imageio.get_writer(
        out,
        fps=FPS,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",
        macro_block_size=1,
    )
    try:
        for img, seconds in slides:
            arr = np.asarray(img)
            n = max(1, int(seconds * FPS))
            for _ in range(n):
                writer.append_data(arr)
    finally:
        writer.close()
    print(f"Wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
