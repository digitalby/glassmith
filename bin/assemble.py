#!/usr/bin/env python3
"""Assemble a spec + layer images into a valid Apple `.icon` bundle.

A `.icon` bundle (Icon Composer / iOS 26 "Liquid Glass") is a directory with:
  - icon.json   the document descriptor
  - Assets/     the referenced SVG/PNG layer files

This script reads an ergonomic spec (see schema/spec.md) and emits a canonical
icon.json faithful to the format, copying every referenced layer into Assets/.

stdlib only. No external dependencies.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

APPEARANCE_FILLS = {"automatic", "system-light", "system-dark"}
SHADOW_KINDS = {"none", "neutral", "layerColor"}
BLEND_MODES = {
    "normal", "multiply", "screen", "overlay", "darken", "lighten",
    "color-dodge", "color-burn", "soft-light", "hard-light", "difference",
    "exclusion", "hue", "saturation", "color", "luminosity",
    "plus-darker", "plus-lighter",
}


class SpecError(Exception):
    """Raised when the input spec is invalid. Reported to the user verbatim."""


def fail(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    raise SpecError(msg)


def resolve_fill(value: Any, *, where: str) -> Any:
    """Map a spec fill shorthand to a canonical icon.json fill value."""
    if value is None:
        return None
    if isinstance(value, str):
        if value in APPEARANCE_FILLS:
            return value
        if ":" in value:  # "display-p3:r,g,b,a" colour string
            return {"solid": value}
        fail(f"{where}: unknown fill '{value}'. Use a colour like "
             f"'display-p3:0.1,0.1,0.2,1.0' or one of {sorted(APPEARANCE_FILLS)}.")
    if isinstance(value, dict):
        keys = set(value)
        if keys <= {"solid", "automatic-gradient"} and len(keys) == 1:
            return value
        fail(f"{where}: fill object must be {{'solid': ...}} or "
             f"{{'automatic-gradient': ...}}, got keys {sorted(keys)}.")
    fail(f"{where}: fill must be a string or object.")


def resolve_shadow(value: Any, *, where: str) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        if value not in SHADOW_KINDS:
            fail(f"{where}: shadow kind '{value}' not in {sorted(SHADOW_KINDS)}.")
        return {"kind": value, "opacity": 1.0}
    if isinstance(value, dict):
        kind = value.get("kind")
        if kind not in SHADOW_KINDS:
            fail(f"{where}: shadow.kind '{kind}' not in {sorted(SHADOW_KINDS)}.")
        return {"kind": kind, "opacity": float(value.get("opacity", 1.0))}
    fail(f"{where}: shadow must be a string or object.")


def resolve_position(value: Any, *, where: str) -> Any:
    if value is None:
        return None
    if not isinstance(value, dict):
        fail(f"{where}: position must be an object {{'scale','translation'}}.")
    scale = float(value.get("scale", 1.0))
    translation = value.get("translation", [0.0, 0.0])
    if not (isinstance(translation, list) and len(translation) == 2):
        fail(f"{where}: position.translation must be [x, y].")
    return {"scale": scale, "translation-in-points": [float(translation[0]), float(translation[1])]}


def resolve_specializations(raw: Any, mapper, *, where: str) -> Any:
    """Map a list of {appearance?, idiom?, value} entries, transforming value."""
    if raw is None:
        return None
    if not isinstance(raw, list):
        fail(f"{where}: specializations must be a list.")
    out = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict) or "value" not in entry:
            fail(f"{where}[{i}]: each specialization needs a 'value'.")
        item: dict[str, Any] = {"value": mapper(entry["value"], where=f"{where}[{i}].value")}
        if "appearance" in entry:
            item["appearance"] = entry["appearance"]
        if "idiom" in entry:
            item["idiom"] = entry["idiom"]
        out.append(item)
    return out


def build_layer(raw: dict[str, Any], assets: dict[str, Path], layers_dir: Path,
                *, where: str) -> dict[str, Any]:
    image = raw.get("image")
    if not image:
        fail(f"{where}: every layer needs an 'image' (filename under the layers dir).")
    src = (layers_dir / image)
    if not src.is_file():
        fail(f"{where}: layer image '{image}' not found at {src}.")
    assets[Path(image).name] = src

    layer: dict[str, Any] = {"image-name": Path(image).name}
    if "name" in raw:
        layer["name"] = raw["name"]
    if "opacity" in raw:
        layer["opacity"] = float(raw["opacity"])
    if "hidden" in raw:
        layer["hidden"] = bool(raw["hidden"])
    if "glass" in raw:
        layer["glass"] = bool(raw["glass"])
    if raw.get("blend_mode"):
        bm = raw["blend_mode"]
        if bm not in BLEND_MODES:
            fail(f"{where}: blend_mode '{bm}' not in {sorted(BLEND_MODES)}.")
        layer["blend-mode"] = bm
    fill = resolve_fill(raw.get("fill"), where=f"{where}.fill")
    if fill is not None:
        layer["fill"] = fill
    position = resolve_position(raw.get("position"), where=f"{where}.position")
    if position is not None:
        layer["position"] = position
    return layer


def build_group(raw: dict[str, Any], idx: int, assets: dict[str, Path],
                layers_dir: Path) -> dict[str, Any]:
    where = f"groups[{idx}]"
    raw_layers = raw.get("layers")
    if not raw_layers:
        fail(f"{where}: group needs at least one layer.")
    group: dict[str, Any] = {
        "layers": [build_layer(l, assets, layers_dir, where=f"{where}.layers[{j}]")
                   for j, l in enumerate(raw_layers)],
    }
    if "name" in raw:
        group["name"] = raw["name"]
    if "hidden" in raw:
        group["hidden"] = bool(raw["hidden"])
    if "specular" in raw:
        group["specular"] = bool(raw["specular"])
    if "opacity" in raw:
        group["opacity"] = float(raw["opacity"])
    if "blur_material" in raw and raw["blur_material"] is not None:
        group["blur-material"] = float(raw["blur_material"])
    if raw.get("lighting"):
        if raw["lighting"] not in {"combined", "individual"}:
            fail(f"{where}: lighting must be 'combined' or 'individual'.")
        group["lighting"] = raw["lighting"]
    if raw.get("blend_mode"):
        if raw["blend_mode"] not in BLEND_MODES:
            fail(f"{where}: blend_mode '{raw['blend_mode']}' invalid.")
        group["blend-mode"] = raw["blend_mode"]
    shadow = resolve_shadow(raw.get("shadow"), where=f"{where}.shadow")
    if shadow is not None:
        group["shadow"] = shadow
    if isinstance(raw.get("translucency"), dict):
        t = raw["translucency"]
        group["translucency"] = {"enabled": bool(t.get("enabled", True)),
                                 "value": float(t.get("value", 0.5))}
    return group


def build_document(spec: dict[str, Any], assets: dict[str, Path],
                   layers_dir: Path) -> dict[str, Any]:
    raw_groups = spec.get("groups")
    if not raw_groups:
        fail("spec: 'groups' is required and must contain at least one group.")
    doc: dict[str, Any] = {
        "groups": [build_group(g, i, assets, layers_dir) for i, g in enumerate(raw_groups)],
    }
    if spec.get("color_space_for_untagged_svg_colors"):
        doc["color-space-for-untagged-svg-colors"] = spec["color_space_for_untagged_svg_colors"]
    fill = resolve_fill(spec.get("background"), where="background")
    if fill is not None:
        doc["fill"] = fill
    fill_spec = resolve_specializations(
        spec.get("background_specializations"), resolve_fill, where="background_specializations")
    if fill_spec is not None:
        doc["fill-specializations"] = fill_spec
    platforms = spec.get("platforms", "shared")
    if platforms == "shared":
        doc["supported-platforms"] = {"squares": "shared"}
    elif isinstance(platforms, list):
        doc["supported-platforms"] = {"squares": {"platforms": platforms}}
    else:
        fail("spec: 'platforms' must be 'shared' or a list of platform names.")
    return doc


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble a .icon bundle from a spec + layers.")
    ap.add_argument("spec", type=Path, help="Path to the icon spec JSON.")
    ap.add_argument("-o", "--output", type=Path, help="Output .icon bundle path "
                    "(default: <name>.icon next to the spec).")
    ap.add_argument("--layers", type=Path, help="Directory holding layer images "
                    "(default: a 'layers' dir next to the spec, else the spec's dir).")
    args = ap.parse_args()

    if not args.spec.is_file():
        print(f"error: spec not found: {args.spec}", file=sys.stderr)
        return 2
    spec = json.loads(args.spec.read_text())

    spec_dir = args.spec.resolve().parent
    layers_dir = args.layers or (spec_dir / "layers" if (spec_dir / "layers").is_dir() else spec_dir)
    name = spec.get("name", "AppIcon")
    out = args.output or (spec_dir / f"{name}.icon")

    assets: dict[str, Path] = {}
    try:
        document = build_document(spec, assets, layers_dir)
    except SpecError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if out.exists():
        shutil.rmtree(out)
    (out / "Assets").mkdir(parents=True)
    (out / "icon.json").write_text(json.dumps(document, indent=2) + "\n")
    for filename, src in assets.items():
        shutil.copy2(src, out / "Assets" / filename)

    print(f"Assembled {out}")
    print(f"  icon.json  : {len(document['groups'])} group(s)")
    print(f"  Assets/    : {len(assets)} layer file(s) -> {', '.join(sorted(assets))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
