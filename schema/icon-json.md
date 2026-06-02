# The `.icon` bundle format

An `.icon` bundle (saved by Apple's Icon Composer, introduced with iOS 26 /
macOS 26) is a **directory**:

```
AppIcon.icon/
├── icon.json        # the document descriptor
└── Assets/          # the layer image files it references (SVG, PNG)
```

`actool` (Xcode 26+) compiles the bundle into an `Assets.car` and emits the
`CFBundleIconName` partial Info.plist. The system renders depth, parallax,
lighting and the Liquid Glass material from the layers at runtime.

> This reference is reconstructed from observed bundles, Apple's documentation,
> and the typed model in [`rozd/icon-kit`](https://github.com/rozd/icon-kit).
> Keys are **kebab-case**.

## Document (`icon.json` root)

| Key | Type | Notes |
|---|---|---|
| `groups` | `Group[]` | Required. Rendered back-to-front. |
| `fill` | `Fill` | Document background. |
| `fill-specializations` | `Specialization<Fill>[]` | Per-appearance / per-idiom background overrides. |
| `color-space-for-untagged-svg-colors` | string | e.g. `"display-p3"`. |
| `supported-platforms` | `SupportedPlatforms` | Platform targeting. |

## Group

Rendered back-to-front. Each visual property has a matching
`<prop>-specializations` array for per-appearance / per-idiom overrides.

| Key | Type | Notes |
|---|---|---|
| `layers` | `Layer[]` | Required. Back-to-front. |
| `id`, `name` | string | Optional identifiers. |
| `hidden` | bool | |
| `shadow` | `Shadow` | |
| `translucency` | `Translucency` | visionOS glass. |
| `blur-material` | number | Blur material strength. |
| `opacity` | number | 0.0–1.0. |
| `lighting` | `"combined"` \| `"individual"` | |
| `specular` | bool | Specular highlight (glass). |
| `blend-mode` | `BlendMode` | |

Specialization arrays: `hidden-specializations`, `shadow-specializations`,
`translucency-specializations`, `opacity-specializations`,
`specular-specializations`, `blend-mode-specializations`,
`position-specializations`.

## Layer

| Key | Type | Notes |
|---|---|---|
| `image-name` | string | Filename in `Assets/`. |
| `id`, `name` | string | Optional. |
| `fill` | `Fill` | |
| `blend-mode` | `BlendMode` | |
| `opacity` | number | 0.0–1.0. |
| `hidden` | bool | |
| `glass` | bool | visionOS glass effect. |
| `position` | `Position` | |

Specialization arrays: `image-name-specializations`, `fill-specializations`,
`blend-mode-specializations`, `opacity-specializations`,
`hidden-specializations`, `glass-specializations`, `position-specializations`.

## Value types

### Fill

Polymorphic:

- String: `"automatic"`, `"system-light"`, `"system-dark"`.
- Object: `{ "solid": "<color>" }` or `{ "automatic-gradient": "<color>" }`.

### Color

A string `"<color-space>:c1,c2,c3,c4"`:

- `srgb`, `extended-srgb`, `display-p3` → `r,g,b,a` (0.0–1.0).
- `gray`, `extended-gray` → `luminance,alpha`.

Examples: `display-p3:1.0,0.0,0.0,1.0`, `gray:0.5,1.0`.

### Position

```json
{ "scale": 1.0, "translation-in-points": [0.0, 0.0] }
```

### Shadow

```json
{ "kind": "neutral", "opacity": 1.0 }
```

`kind`: `none` · `neutral` · `layerColor`.

### Translucency

```json
{ "enabled": true, "value": 0.5 }
```

### BlendMode

`normal`, `multiply`, `screen`, `overlay`, `darken`, `lighten`, `color-dodge`,
`color-burn`, `soft-light`, `hard-light`, `difference`, `exclusion`, `hue`,
`saturation`, `color`, `luminosity`, `plus-darker`, `plus-lighter`.

### SupportedPlatforms

```json
{ "circles": ["watchOS"], "squares": "shared" }
```

`squares` is either the string `"shared"` or `{ "platforms": ["iOS", "macOS"] }`.

### Specialization

```json
{ "appearance": "dark", "idiom": "iOS", "value": <T> }
```

`appearance`: `light` · `dark` · `tinted` (omit for all).
`idiom`: `square` · `macOS` · `iOS` · `watchOS` · `visionOS` (omit for all).

Resolution priority (highest first): exact (appearance+idiom) → appearance-only →
idiom-only → default (both omitted) → the base value.
