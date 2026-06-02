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
- ❌ Do not commit Apple's rendered symbol pixels to a repo you publish.
- ❌ Do not submit an SF-Symbol-derived icon to the App Store.

For the shipped icon, draw original artwork (see `examples/demo/` for a fully
original clip-art clock) and feed that through the same pipeline.

## Why glassmith doesn't bundle a rendered symbol

The `examples/sf-symbol/` example references `layers/symbol.png` but does **not**
commit it (it's git-ignored). You generate it locally with the `sf` command. That
keeps Apple's artwork out of this MIT-licensed repo and keeps the example honest
about the restriction above.
