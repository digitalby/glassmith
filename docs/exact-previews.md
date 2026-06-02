# Roadmap: pixel-exact previews

`bin/glassmith preview` renders **faithful approximations** with `rsvg-convert`:
correct for composition, colour, depth order and legibility, but not the exact
Liquid Glass refraction/specular model, which only the OS renderer produces.

For pixel-exact output we want a second, slower path that uses Apple's renderer.

## Approach

1. Generate a throwaway iOS app target whose app icon is the `.icon` under test
   (reuse `bin/integrate.rb` against a scratch project, or template one).
2. `xcodebuild` it for an iOS 26 simulator.
3. Boot the simulator, install, and capture the Home Screen / Settings icon with
   `xcrun simctl io <udid> screenshot`, cropping to the icon rect.
4. Repeat under light, dark and tinted system appearances
   (`xcrun simctl ui <udid> appearance dark`, etc.).

## Why it isn't the default

It needs a booted simulator and a full build per run — seconds-to-minutes versus
the instant SVG path. The approximation is the right default for the tight
design-review loop; exact previews are the confirmation pass before shipping.

## Wanted

A `bin/glassmith preview --fidelity exact` flag implementing the above, with the
scratch project cached between runs. See CONTRIBUTING.md.
