chmod +x "$HERE/build_mac.sh" 2>/dev/null || true
#!/usr/bin/env bash
# Build script for macOS: creates a single-file executable using PyInstaller.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
cd "$ROOT"

echo "Creating virtualenv..."
python3 -m venv .venv_build
source .venv_build/bin/activate
pip install --upgrade pip
pip install -r requirements-build.txt

echo "Running pyinstaller..."
# Entry point is src/jedi_fugitive/main.py which defines main()
pyinstaller --noconfirm --onefile --name "jedi-fugitive" src/jedi_fugitive/main.py

echo "Build finished. Dist artifact is in dist/jedi-fugitive"
echo "You can copy dist/jedi-fugitive to target machines and run it from a terminal."

deactivate
