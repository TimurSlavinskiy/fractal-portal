#!/usr/bin/env python3
"""FRACTAL PORTAL — deterministic Julia-set mathematical artwork.

Every RGB pixel is computed from the iteration z_(n+1) = z_n**2 + c,
its complex derivative and a smooth escape-time / distance estimate.
Only NumPy and Pillow are required; no generative image model or assets.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


# Complex constants determine the geometry. Edit these to explore!
PRESETS = {
    "aurora": {"c": complex(-0.8, 0.156), "zoom": 1.09, "palette": "aurora"},
    "ember": {"c": complex(-0.74543, 0.11301), "zoom": 1.08, "palette": "ember"},
    "coral": {"c": complex(-0.70176, -0.3842), "zoom": 1.08, "palette": "coral"},
}
COLORS = {
    "aurora": ((20, 234, 242), (215, 72, 248), (255, 180, 95)),
    "ember": ((255, 83, 96), (255, 200, 78), (225, 80, 245)),
    "coral": ((36, 249, 185), (75, 138, 255), (255, 194, 97)),
}


def render(
    width: int = 1600,
    height: int = 1000,
    *,
    c: complex = complex(-0.8, 0.156),
    zoom: float = 1.09,
    center_x: float = 0,
    center_y: float = 0,
    iterations: int = 230,
    palette: str = "aurora",
    supersample: int = 1,
) -> Image.Image:
    """Return a reproducible RGB image, with no external artwork or randomness."""
    if not 128 <= width <= 4096 or not 128 <= height <= 4096:
        raise ValueError("Width and height must be between 128 and 4096")
    if iterations < 30 or iterations > 1500:
        raise ValueError("Iterations must be between 30 and 1500")
    if supersample not in (1, 2):
        raise ValueError("Supersample must be 1 or 2")
    if not np.isfinite([zoom, center_x, center_y, c.real, c.imag]).all() or zoom <= 0:
        raise ValueError("Coordinates, zoom, and c must be finite; zoom must be positive")
    if palette not in COLORS:
        raise ValueError(f"Unknown palette: {palette}")

    w, h = width * supersample, height * supersample
    if w * h > 14_000_000:
        raise ValueError("Resolution is too large; lower size or supersampling")

    # Use square world units, regardless of the image aspect ratio.
    # The +0.5 samples the CENTER of each pixel.
    yy, xx = np.ogrid[:h, :w]
    pixel_size = 3.45 / (zoom * w)
    zx = (xx + 0.5 - w / 2) * pixel_size + center_x
    zy = (h / 2 - yy - 0.5) * pixel_size + center_y
    z = np.array(zx + 1j * zy, dtype=np.complex128)

    derivative = np.ones((h, w), dtype=np.complex128)
    active = np.ones((h, w), dtype=bool)
    smooth_escape = np.zeros((h, w), dtype=np.float64)
    distance = np.full((h, w), 1e5, dtype=np.float64)
    escape_angle = np.zeros((h, w), dtype=np.float64)
    bailout = 16.0

    # Iterate only points that have not escaped. For a Julia set,
    # dz_(n+1)/dz_0 = 2*z_n*(dz_n/dz_0).
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        for iteration in range(iterations):
            derivative[active] *= 2 * z[active]
            z[active] = z[active] * z[active] + c
            modulus = np.abs(z)
            escaping = active & (modulus > bailout)
            if escaping.any():
                radius = modulus[escaping]
                smooth_escape[escaping] = (
                    iteration + 2 - np.log2(np.log(radius))
                )
                distance[escaping] = (
                    radius * np.log(radius) / np.maximum(np.abs(derivative[escaping]), 1e-100)
                )
                escape_angle[escaping] = np.angle(z[escaping])
                active[escaping] = False
            if not active.any():
                break

    # Convert fractal-distance estimate to pixel units so the glow has
    # approximately the same visual width at any export resolution.
    dp = np.maximum(distance / pixel_size, 0.0)
    fine = np.exp(-np.power(dp / 1.6, 0.7))

    # A continuous palette based on smooth escape-time and escape direction.
    t = 0.5 + 0.5 * np.cos(0.205 * smooth_escape + 0.45 * escape_angle)
    accent = np.power(0.5 + 0.5 * np.cos(0.41 * smooth_escape - 0.65 * escape_angle + 1.8), 8)
    primary, secondary, highlight = (np.asarray(c_, dtype=float) for c_ in COLORS[palette])
    color = (
        primary[None, None, :] * t[:, :, None]
        + secondary[None, None, :] * (1 - t[:, :, None])
    )
    color = color * (1 - 0.42 * accent[:, :, None]) + highlight[None, None, :] * (0.42 * accent[:, :, None])

    # Dark, gently shaded background. RGB is computed, not sampled from images.
    xn = (np.arange(w)[None, :] + 0.5 - w / 2) / w
    yn = (np.arange(h)[:, None] + 0.5 - h / 2) / w
    cloud = np.exp(-((xn + 0.28)**2 / 0.22 + (yn - 0.07)**2 / 0.075))
    bg = np.empty((h, w, 3), dtype=np.float32)
    bg[:, :, 0] = 4 + 10 * cloud
    bg[:, :, 1] = 5 + 5 * cloud
    bg[:, :, 2] = 15 + 25 * cloud

    # Illuminate the intricate boundary. Diffuse halos are BLURRED from the
    # fine boundary itself, rather than using a large raw distance estimate;
    # that avoids visible escape-iteration banding in the surrounding glow.
    boundary = color * fine[:, :, None]
    source = Image.fromarray(np.uint8(np.clip(boundary * 0.72, 0, 255)))
    small_halo = np.asarray(source.filter(ImageFilter.GaussianBlur(9 * supersample)), dtype=np.float32)
    large_halo = np.asarray(source.filter(ImageFilter.GaussianBlur(32 * supersample)), dtype=np.float32)
    bg += small_halo * 0.70 + large_halo * 0.75
    bg += boundary * 1.20
    bg += fine[:, :, None] * np.array([28.0, 35.0, 37.0])
    # Unescaped points belong to the (approximated) filled Julia set.
    bg[active] = (3, 4, 12)
    image = Image.fromarray(np.uint8(np.clip(bg, 0, 255)))
    if supersample == 2:
        image = image.resize((width, height), Image.Resampling.LANCZOS)
    return image


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preset", choices=tuple(PRESETS), default="aurora")
    p.add_argument("--width", type=int, default=1600)
    p.add_argument("--height", type=int, default=1000)
    p.add_argument("--iterations", type=int, default=230)
    p.add_argument("--zoom", type=float, default=None)
    p.add_argument("--center-x", type=float, default=0.0)
    p.add_argument("--center-y", type=float, default=0.0)
    p.add_argument("--real", type=float, default=None, help="Real part of Julia constant c")
    p.add_argument("--imag", type=float, default=None, help="Imaginary part of Julia constant c")
    p.add_argument("--palette", choices=tuple(COLORS), default=None)
    p.add_argument("--supersample", type=int, choices=(1, 2), default=1)
    p.add_argument("--output", type=Path, default=Path("fractal_aurora.png"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    chosen = PRESETS[args.preset]
    const = chosen["c"]
    if args.real is not None or args.imag is not None:
        const = complex(
            args.real if args.real is not None else const.real,
            args.imag if args.imag is not None else const.imag,
        )
    image = render(
        args.width, args.height, c=const,
        zoom=args.zoom if args.zoom is not None else chosen["zoom"],
        center_x=args.center_x, center_y=args.center_y,
        iterations=args.iterations,
        palette=args.palette or chosen["palette"],
        supersample=args.supersample,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output, format="PNG", optimize=True)
    print(f"Generated {args.output} — {image.width} x {image.height} RGB, c={const}")


if __name__ == "__main__":
    main()
