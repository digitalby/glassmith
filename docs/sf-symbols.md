# SF Symbols as a layer source (prototyping)

`bin/glassmith sf` renders any SF Symbol to a transparent PNG layer you can feed
straight into the pipeline. It uses AppKit (`NSImage(systemSymbolName:)`) via the
Xcode Swift toolchain, no GUI.

```sh
glassmith sf clock.fill --out layers/symbol.png --color "#FFFFFF" --weight semibold --scale 0.56
glassmith assemble icon.spec.json -o SFGlass.icon
glassmith preview SFGlass.icon
```

Flags: `--color "#RRGGBB"`, `--weight regular|medium|semibold|bold|heavy|black`,
`--size <px>` (default 1024), `--scale <0..1>` (glyph size as a fraction of the
canvas).

## ⚠️ License: do not ship an SF Symbol as your app icon

Apple's [SF Symbols license](https://developer.apple.com/fonts/) **prohibits
using SF Symbols — or modified versions of them — in app icons, logos, or
trademarks.** An App Store icon built from an SF Symbol can get your app
rejected.

So treat this source as **prototyping only**:

- ✅ Mock up layout, background, colour and the glass treatment fast.
- ✅ Explore depth/specular before commissioning real art.
- ✅ Show a rendered symbol in docs/marketing to *illustrate the tool* (the
  README hero does this) — that's the common, accepted use.
- ❌ Do not submit an SF-Symbol-derived icon to the App Store.

For the shipped icon, draw original artwork (see `examples/demo/` for a fully
original clip-art clock) and feed that through the same pipeline.

## What this repo commits, and what it doesn't

- The README hero is a **composited illustration** of an SF Symbol on glass —
  fine as documentation of what the tool does.
- The `examples/sf-symbol/` example references `layers/symbol.png` but does
  **not** commit the raw layer (it's git-ignored). You generate it locally with
  the `sf` command, so the bare Apple glyph asset isn't redistributed here and
  the example stays honest about the restriction above.
