#!/usr/bin/env bash
# Compile / validate a .icon bundle with actool, producing an Assets.car.
#
# Validation is the fast pre-flight gate: if actool accepts the bundle, the
# icon.json + Assets are well-formed for the installed Xcode toolchain. This is
# the source of truth, not a JSON linter.
#
# Usage:
#   compile.sh validate <bundle.icon>
#   compile.sh compile  <bundle.icon> <output-dir> [--platform iphoneos] [--min 26.0]
#
# Env overrides:
#   ACTOOL          path to actool (default: xcrun actool)
#   ACTOOL_DEVICES  space-separated --target-device values (default: "iphone ipad")
set -euo pipefail

ACTOOL=${ACTOOL:-"xcrun actool"}
PLATFORM="iphoneos"
MINDT="26.0"
DEVICES=${ACTOOL_DEVICES:-"iphone ipad"}

cmd=${1:-}; shift || true
case "$cmd" in
  validate) BUNDLE=${1:-}; shift || true; OUT=$(mktemp -d) ;;
  compile)  BUNDLE=${1:-}; OUT=${2:-}; shift 2 || true ;;
  *) echo "usage: compile.sh {validate|compile} <bundle.icon> [output-dir]" >&2; exit 2 ;;
esac

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform) PLATFORM=$2; shift 2 ;;
    --min) MINDT=$2; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
done

[[ -d "$BUNDLE" && -f "$BUNDLE/icon.json" ]] || { echo "error: not a .icon bundle: $BUNDLE" >&2; exit 2; }
[[ -n "${OUT:-}" ]] || { echo "error: missing output dir" >&2; exit 2; }
mkdir -p "$OUT"

NAME=$(basename "$BUNDLE"); NAME=${NAME%.icon}
PLIST="$OUT/partial-info.plist"

device_args=(); for d in $DEVICES; do device_args+=(--target-device "$d"); done

set -x
$ACTOOL "$BUNDLE" \
  --compile "$OUT" \
  --app-icon "$NAME" \
  --include-all-app-icons \
  --platform "$PLATFORM" \
  --minimum-deployment-target "$MINDT" \
  "${device_args[@]}" \
  --output-partial-info-plist "$PLIST" \
  --errors --warnings --notices \
  --output-format human-readable-text
set +x

echo
if [[ -f "$OUT/Assets.car" ]]; then
  echo "OK: $OUT/Assets.car ($(du -h "$OUT/Assets.car" | cut -f1))"
  [[ -f "$PLIST" ]] && echo "Partial Info.plist keys:" && /usr/libexec/PlistBuddy -c Print "$PLIST" 2>/dev/null || true
else
  echo "error: actool did not produce Assets.car" >&2; exit 1
fi

[[ "$cmd" == "validate" ]] && rm -rf "$OUT"
exit 0
