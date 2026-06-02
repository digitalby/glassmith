# SF Symbol example (prototyping)

This example builds a glass icon from an SF Symbol. The rendered symbol is **not
committed** (Apple's SF Symbols license forbids redistributing the artwork and
forbids using it in app icons). Generate it locally:

```sh
mkdir -p layers
../../bin/glassmith sf clock.fill --out layers/symbol.png --color "#FFFFFF" --weight semibold --scale 0.56
../../bin/glassmith assemble icon.spec.json -o SFGlass.icon
../../bin/glassmith preview SFGlass.icon
open SFGlass.icon/.previews
```

Read the license caveat first: [`docs/sf-symbols.md`](../../docs/sf-symbols.md).
Prototyping is fine; **don't ship an SF Symbol as a real app icon.**
