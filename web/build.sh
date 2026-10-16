#!/usr/bin/env bash
# Build the browser version into web/dist: the page, the game's Python source
# (as JSON) and the Pyodide runtime it runs on. Serve web/dist with any static
# server, e.g.  python3 -m http.server -d web/dist 8000
set -euo pipefail
cd "$(dirname "$0")/.."
PYODIDE_VERSION=0.26.4
OUT=web/dist
rm -rf "$OUT" && mkdir -p "$OUT/pyodide"
cp web/index.html "$OUT/index.html"
python3 - "$OUT/game.json" <<'PY'
import json, pathlib, sys
root = pathlib.Path('src')
files = {str(p.relative_to(root)): p.read_text(encoding='utf-8')
         for p in sorted(root.glob('jedi_fugitive/**/*.py'))
         if '__pycache__' not in p.parts and 'gfx' not in p.parts}
pathlib.Path(sys.argv[1]).write_text(json.dumps(files), encoding='utf-8')
PY
tmp=$(mktemp -d)
(cd "$tmp" && npm pack "pyodide@$PYODIDE_VERSION" >/dev/null && tar xzf "pyodide-$PYODIDE_VERSION.tgz")
cp "$tmp"/package/{pyodide.js,pyodide.asm.js,pyodide.asm.wasm,pyodide-lock.json} "$OUT/pyodide/"
# hosts that refuse .zip still serve .wasm; Pyodide reads the stdlib as plain bytes
cp "$tmp"/package/python_stdlib.zip "$OUT/pyodide/python_stdlib.wasm"
rm -rf "$tmp"
echo "Built $OUT ($(du -sh "$OUT" | cut -f1))"
