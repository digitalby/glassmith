#!/usr/bin/env python3
"""Render review previews of a `.icon` bundle across appearance variants.

For the human review gate: composites the bundle's layers, back-to-front, onto a
rounded-rect (squircle approximation) background and rasterises one PNG per
appearance: light, dark, tinted, and clear.

These are FAITHFUL APPROXIMATIONS, not Apple's renderer. They are correct for
judging composition, colour, depth order and legibility. They do not reproduce
the exact Liquid Glass refraction/specular model (that only comes from the OS).
For pixel-exact output, build the .icon in a throwaway target and screenshot the
simulator (see docs/exact-previews.md, a tracked roadmap item).

Only dependency: rsvg-convert. Layers are inlined as base64 data URIs so no
external file references are needed (avoids librsvg's resource sandbox).
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

APPEARANCES = ["light", "dark", "tinted", "clear"]
CORNER_RATIO = 0.2237  # iOS continuous-corner radius as a fraction of icon size


def parse_color(value: str) -> tuple[int, int, int, float]:
    """Parse 'space:c1,c2,c3,c4' (or grayscale 'gray:l,a') to (r,g,b,a) 0-255/0-1."""
    space, _, comps_raw = value.partition(":")
    comps = [float(c) for c in comps_raw.split(",")]
    if space in ("gray", "extended-gray"):
        lum = comps[0]
        a = comps[1] if len(comps) > 1 else 1.0
        v = max(0, min(255, round(lum * 255)))
        return v, v, v, a
    r, g, b = (max(0, min(255, round(c * 255))) for c in comps[:3])
    a = comps[3] if len(comps) > 3 else 1.0
    return r, g, b, a


def lighten(c: tuple[int, int, int, float], f: float) -> tuple[int, int, int, float]:
    r, g, b, a = c
    return (round(r + (255 - r) * f), round(g + (255 - g) * f), round(b + (255 - b) * f), a)


def darken(c: tuple[int, int, int, float], f: float) -> tuple[int, int, int, float]:
    r, g, b, a = c
    return (round(r * (1 - f)), round(g * (1 - f)), round(b * (1 - f)), a)


def fill_to_color(fill: Any) -> tuple[int, int, int, float] | None:
    """A document/spec fill value -> rgba, or None if it carries no explicit colour."""
    if fill is None:
        return None
    if isinstance(fill, dict):
        col = fill.get("solid") or fill.get("automatic-gradient")
        return parse_color(col) if col else None
    if fill == "system-dark":
        return (28, 28, 30, 1.0)
    if fill == "system-light":
        return (242, 242, 247, 1.0)
    return None  # "automatic" -> let the appearance decide


def spec_fill(doc: dict[str, Any], appearance: str) -> Any:
    for spec in doc.get("fill-specializations", []) or []:
        if spec.get("appearance") == appearance and spec.get("idiom") is None:
            return spec["value"]
    return None


# How each appearance treats the icon. `backdrop_replaces` means the OS supplies
# the background and the artist's own background fill is dropped (tinted, clear).
APPEARANCE = {
    "light": {"mono": False, "alpha": 1.0, "specular": 1.0, "backdrop_replaces": None},
    "dark": {"mono": False, "alpha": 1.0, "specular": 1.0, "backdrop_replaces": None},
    "tinted": {"mono": True, "alpha": 1.0, "specular": 0.7, "backdrop_replaces": (22, 22, 24, 1.0)},
    "clear": {"mono": True, "alpha": 0.55, "specular": 1.7, "backdrop_replaces": (70, 74, 82, 1.0)},
}


def appearance_bg(doc: dict[str, Any], appearance: str) -> tuple[int, int, int, float]:
    """Resolve the background for an appearance, faithfully to how iOS composites."""
    cfg = APPEARANCE[appearance]
    if cfg["backdrop_replaces"] is not None and spec_fill(doc, appearance) is None:
        # tinted / clear: the system supplies a neutral backdrop; icon bg is dropped.
        return cfg["backdrop_replaces"]
    explicit = fill_to_color(spec_fill(doc, appearance))
    if explicit is not None:
        return explicit
    base = fill_to_color(doc.get("fill"))
    if base is None:
        return (242, 242, 247, 1.0) if appearance == "light" else (20, 20, 22, 1.0)
    if appearance == "dark":  # no explicit dark variant: derive one by darkening.
        return darken(base, 0.5)
    return base


def data_uri(path: Path) -> str:
    mime = "image/svg+xml" if path.suffix.lower() == ".svg" else "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def layer_svg(layer: dict[str, Any], assets: Path, size: int, mono: bool) -> str:
    name = layer.get("image-name")
    src = assets / name
    if not src.is_file():
        return ""
    opacity = float(layer.get("opacity", 1.0))
    pos = layer.get("position", {})
    scale = float(pos.get("scale", 1.0))
    tx, ty = (pos.get("translation-in-points", [0.0, 0.0]) + [0.0, 0.0])[:2]
    off = (size - size * scale) / 2  # centre-anchored scale + translate
    transform = f"translate({off + tx},{off + ty}) scale({scale})"
    flt = ' filter="url(#mono)"' if mono else ""
    return (f'<g transform="{transform}" opacity="{opacity}"{flt}>'
            f'<image href="{data_uri(src)}" x="0" y="0" width="{size}" height="{size}" '
            f'preserveAspectRatio="xMidYMid meet"/></g>')


def build_svg(doc: dict[str, Any], assets: Path, size: int, appearance: str) -> str:
    cfg = APPEARANCE[appearance]
    r, g, b, a = appearance_bg(doc, appearance)
    radius = size * CORNER_RATIO
    spec_alpha = 0.35 * cfg["specular"]
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">',
        # mono: luminance grayscale (tinted/clear). Bright art stays bright, dark recedes.
        '<defs>'
        f'<clipPath id="squircle"><rect x="0" y="0" width="{size}" height="{size}" '
        f'rx="{radius:.2f}" ry="{radius:.2f}"/></clipPath>'
        '<filter id="mono"><feColorMatrix type="matrix" '
        'values="0.33 0.5 0.16 0 0  0.33 0.5 0.16 0 0  0.33 0.5 0.16 0 0  0 0 0 1 0"/></filter>'
        f'<radialGradient id="bg" cx="0.4" cy="0.32" r="0.95">'
        f'<stop offset="0%" stop-color="rgb{lighten((r,g,b,a),0.14)[:3]}"/>'
        f'<stop offset="100%" stop-color="rgb({r},{g},{b})"/></radialGradient>'
        '<radialGradient id="specular" cx="0.30" cy="0.24" r="0.9">'
        f'<stop offset="0%" stop-color="#ffffff" stop-opacity="{spec_alpha:.2f}"/>'
        f'<stop offset="45%" stop-color="#ffffff" stop-opacity="{spec_alpha * 0.18:.2f}"/>'
        '<stop offset="100%" stop-color="#ffffff" stop-opacity="0"/></radialGradient>'
        '</defs>',
        '<g clip-path="url(#squircle)">',
        f'<rect x="0" y="0" width="{size}" height="{size}" fill="url(#bg)" fill-opacity="{a}"/>',
    ]
    for group in doc.get("groups", []):
        if group.get("hidden"):
            continue
        gopacity = float(group.get("opacity", 1.0)) * cfg["alpha"]
        parts.append(f'<g opacity="{gopacity}">')
        for layer in group.get("layers", []):
            if layer.get("hidden"):
                continue
            parts.append(layer_svg(layer, assets, size, cfg["mono"]))
        parts.append('</g>')
    parts.append(f'<rect x="0" y="0" width="{size}" height="{size}" fill="url(#specular)"/>')
    parts.append('</g></svg>')
    return "".join(parts)


def render(doc: dict[str, Any], assets: Path, out_dir: Path, name: str,
           sizes: list[int], appearances: list[str]) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for appearance in appearances:
        svg = build_svg(doc, assets, max(sizes), appearance)
        svg_path = out_dir / f"{name}.{appearance}.svg"
        svg_path.write_text(svg)
        for size in sizes:
            png = out_dir / (f"{name}.{appearance}.png" if len(sizes) == 1
                             else f"{name}.{appearance}.{size}.png")
            subprocess.run(
                ["rsvg-convert", "-w", str(size), "-h", str(size), "-o", str(png), str(svg_path)],
                check=True)
            written.append(png)
        svg_path.unlink()
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description="Render appearance previews of a .icon bundle.")
    ap.add_argument("bundle", type=Path, help="Path to the .icon bundle.")
    ap.add_argument("-o", "--output", type=Path, help="Output directory for PNGs "
                    "(default: <bundle>/.previews).")
    ap.add_argument("--size", type=int, action="append", help="Output size(s) in px "
                    "(repeatable; default 1024).")
    ap.add_argument("--appearance", action="append", choices=APPEARANCES,
                    help="Appearance(s) to render (repeatable; default: all).")
    args = ap.parse_args()

    icon_json = args.bundle / "icon.json"
    assets = args.bundle / "Assets"
    if not icon_json.is_file():
        print(f"error: no icon.json in {args.bundle}", file=sys.stderr)
        return 2
    doc = json.loads(icon_json.read_text())
    name = args.bundle.stem
    out_dir = args.output or (args.bundle / ".previews")
    sizes = args.size or [1024]
    appearances = args.appearance or APPEARANCES

    written = render(doc, assets, out_dir, name, sizes, appearances)
    print(f"Rendered {len(written)} preview(s) to {out_dir}:")
    for p in written:
        print(f"  {p.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
