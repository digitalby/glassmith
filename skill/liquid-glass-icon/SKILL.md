---
name: liquid-glass-icon
description: >-
  Use when building, previewing, or installing an iOS 26 / macOS 26 "Liquid
  Glass" app icon (an Icon Composer `.icon` bundle) from layered source art the
  user provides. Triggers on: "build a liquid glass icon", "make an iOS 26
  icon", "assemble a .icon bundle", "preview my app icon in light/dark/tinted",
  "swap in the new glass icon", "integrate this icon into the app". Drives the
  glassmith pipeline: assemble layers into a valid `.icon`, render appearance
  previews for human review, validate with actool, then wire it into an Xcode
  project. ALWAYS hands previews off for explicit approval before touching a
  project, and never compiles into or writes to a project without confirmation.
---

# Liquid Glass icon pipeline

Forge an iOS 26 / macOS 26 Liquid Glass app icon from **layered source the user
provides** (SVG preferred, PNG accepted), then integrate it into an Xcode 26+
project. This skill orchestrates the `glassmith` CLI in `bin/`.

## What a `.icon` is

A directory bundle: `icon.json` (the descriptor) + `Assets/` (layer files).
`icon.json` is `{ groups[] -> layers[] }` with a document `fill` (the
background), per-group `specular` / `shadow` / `lighting` / `blur-material`, and
`*-specializations` arrays that override values per `appearance` (light, dark,
tinted) and `idiom` (iOS, macOS, watchOS, ...). Colours are
`display-p3:r,g,b,a`. See `schema/icon-json.md` for the full schema.

The system renders depth, parallax and the glass material at runtime from these
layers. You supply flat layers; you do NOT bake in highlights or shadows.

## Pipeline (run in order)

Let `GM="$(git rev-parse --show-toplevel)/bin/glassmith"` (or the installed path).

1. **Collect source.** Confirm with the user: the layers (filenames), the
   background colour(s), and which groups/layers map to depth. If they have no
   spec yet, write one to `icon.spec.json` next to a `layers/` dir. The spec
   format is documented in `schema/spec.md`; `examples/demo/` is a complete
   example.

2. **Assemble.** `"$GM" assemble icon.spec.json -o AppIcon.icon`
   Produces a valid bundle. Read back `AppIcon.icon/icon.json` and sanity-check
   the layer order (back-to-front) and background.

3. **Preview + HAND OFF FOR REVIEW.** `"$GM" preview AppIcon.icon`
   Renders `light`, `dark`, `tinted`, `clear` PNGs into `AppIcon.icon/.previews`.
   **Show these to the user and stop.** State plainly that they are faithful
   *approximations* (composition / colour / depth / legibility are accurate; the
   exact glass refraction only appears on-device). Iterate on the spec and
   re-preview until the user explicitly approves. Do not proceed past this gate
   without a clear "yes".

4. **Validate.** `"$GM" validate AppIcon.icon`
   Runs `actool` as a pre-flight. If it does not produce `Assets.car`, fix the
   bundle before going near a project. This is the source of truth, not a linter.

5. **Integrate (only after approval + confirmation).**
   First a dry run, always:
   `"$GM" integrate --project App.xcodeproj --target App --icon AppIcon.icon`
   Show the plan. Then, **only on explicit confirmation**, apply with `--write`.
   It backs up `project.pbxproj` to `*.glassmith.bak`, copies the bundle in, adds
   it to the target's resources, and sets `ASSETCATALOG_COMPILER_APPICON_NAME`.

## Hard gates (do not cross without an explicit yes)

- Never skip the preview hand-off. The user reviews every appearance before any
  compile-into-project or write.
- Never run `integrate --write` without showing the dry-run plan and getting
  confirmation. It mutates `project.pbxproj`.
- Do not modify store-listing metadata, bump versions, archive, or upload. This
  skill stops at "the new icon is wired into the project, build it." Shipping is
  a separate, separately-confirmed step.
- Treat each app as its own decision. Approval for one app's icon is not
  approval for another's.

## Notes

- `"$GM" doctor` checks the toolchain (python3, rsvg-convert, ruby + xcodeproj
  gem, actool). Run it first if anything errors.
- Tinted previews approximate Apple's monochrome treatment by desaturating
  layers; the on-device result derives from layer luminance.
- For pixel-exact previews, build the `.icon` in a throwaway target and
  screenshot the simulator (roadmap: `docs/exact-previews.md`).
