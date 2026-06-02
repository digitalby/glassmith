#!/usr/bin/env bash
# Build the bundled demo end-to-end into a working directory you can inspect.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
DEST=${1:-"$ROOT/examples/demo/out"}

mkdir -p "$DEST"
echo "==> assemble"
python3 "$HERE/assemble.py" "$ROOT/examples/demo/icon.spec.json" -o "$DEST/DemoClock.icon"
echo "==> preview"
python3 "$HERE/preview.py" "$DEST/DemoClock.icon" -o "$DEST/previews"
echo "==> validate (actool)"
"$HERE/compile.sh" validate "$DEST/DemoClock.icon" || {
  echo "validate failed - see actool output above" >&2; exit 1; }
echo
echo "Done. Open the previews:"
echo "  open $DEST/previews"
