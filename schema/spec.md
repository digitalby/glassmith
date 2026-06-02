# The glassmith spec

`icon.spec.json` is an ergonomic wrapper over `icon.json` (see
[`icon-json.md`](icon-json.md)). `bin/glassmith assemble` reads it, copies your
layers into `Assets/`, and emits a canonical, validated `icon.json`.

Layer images are resolved relative to the `--layers` directory (default: a
`layers/` folder next to the spec, else the spec's own directory).

## Top level

| Field | Type | Default | Notes |
|---|---|---|---|
| `name` | string | `"AppIcon"` | Bundle basename → `<name>.icon`. |
| `platforms` | `"shared"` \| string[] | `"shared"` | `"shared"` or e.g. `["iOS","macOS"]`. |
| `background` | fill shorthand | none | Document background. |
| `background_specializations` | spec[] | none | Per-appearance background overrides. |
| `color_space_for_untagged_svg_colors` | string | none | e.g. `"display-p3"`. |
| `groups` | group[] | **required** | Rendered back-to-front. |

## Fill shorthand

`background`, `*_specializations[].value`, and layer `fill` accept:

- a colour string — `"display-p3:0.07,0.09,0.16,1.0"` → `{ "solid": ... }`
- an appearance keyword — `"automatic"`, `"system-light"`, `"system-dark"`
- an explicit object — `{ "automatic-gradient": "display-p3:..." }`

## Group

| Field | Type | Notes |
|---|---|---|
| `layers` | layer[] | **required**, back-to-front. |
| `name` | string | |
| `specular` | bool | Glass specular highlight. |
| `shadow` | `"none"`\|`"neutral"`\|`"layerColor"` or `{kind,opacity}` | |
| `lighting` | `"combined"`\|`"individual"` | |
| `blur_material` | number | |
| `opacity` | number | 0.0–1.0. |
| `blend_mode` | string | See BlendMode in the format doc. |
| `translucency` | `{enabled,value}` | visionOS. |
| `hidden` | bool | |

## Layer

| Field | Type | Notes |
|---|---|---|
| `image` | string | **required** — filename under the layers dir. |
| `name` | string | |
| `opacity` | number | 0.0–1.0. |
| `blend_mode` | string | |
| `fill` | fill shorthand | |
| `position` | `{ "scale": 1.0, "translation": [x, y] }` | |
| `hidden` | bool | |
| `glass` | bool | visionOS. |

## Specialization entries

`background_specializations` is a list of:

```json
{ "appearance": "dark", "idiom": "iOS", "value": "<fill shorthand>" }
```

Omit `appearance` and/or `idiom` to widen the match. See the resolution order in
the format doc.

## Example

See [`examples/demo/icon.spec.json`](../examples/demo/icon.spec.json) and its
`layers/`.

## Design notes

- Provide **flat** layers. Don't bake in highlights, shadows or the glass sheen —
  the OS generates those from your layers at runtime.
- SVG is preferred (scales cleanly across every rendered size). PNG works; supply
  it at 1024×1024 or larger.
- Order matters: the first layer in a group is the **backmost**.
