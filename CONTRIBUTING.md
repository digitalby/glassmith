# Contributing to glassmith

Thanks for helping forge better icons. This project is small, dependency-light,
and meant to stay that way.

## Principles

- **stdlib first.** `assemble.py` and `preview.py` use only the Python standard
  library. Don't add pip dependencies without a strong reason and a discussion.
- **The compiler is the source of truth.** A bundle is "valid" when `actool`
  produces an `Assets.car`, not when a linter is happy. New format support must
  round-trip through `bin/glassmith validate`.
- **Faithful to the format.** `icon.json` keys are kebab-case and mirror Icon
  Composer. When in doubt, check `schema/icon-json.md` and a real `.icon`.
- **Reviewable + safe.** The preview gate and the dry-run-by-default integration
  are features, not friction. Don't remove them.

## Dev loop

```sh
bin/glassmith doctor     # confirm your toolchain
bin/glassmith demo       # full pipeline on the bundled example
```

Add a fixture under `examples/` for any new spec capability and make sure
`bin/glassmith demo` (and CI) still compiles it.

## Good first issues

- **Pixel-exact previews** via the iOS simulator (see `docs/exact-previews.md`).
- **Layer `blend-mode` in previews** — currently carried into `icon.json` but
  rendered as `normal` in the approximation.
- **SVG validation** — warn on layers that reference external resources or fonts
  that won't rasterise deterministically.
- **Android adaptive icons** — a parallel `assemble`/`preview` path.

## Pull requests

- One focused change per PR. Describe what you changed and why.
- Keep `README.md` and the `schema/` docs in sync with behaviour changes.
- No generated build output in commits (see `.gitignore`).

## Code of conduct

Be decent. Assume good faith. We follow the
[Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
