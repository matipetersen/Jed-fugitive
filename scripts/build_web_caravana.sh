#!/usr/bin/env bash
# Empaqueta LA CARAVANA para el navegador/móvil con pygbag (necesita internet: descarga el runtime de pygame-web).
#   pip install pygbag
#   ./scripts/build_web_caravana.sh          # genera build_web/app/build/web
#   python -m pygbag build_web/app           # (alternativa) sirve en http://localhost:8000
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf build_web && mkdir -p build_web/app
cp -r caravana build_web/app/caravana
find build_web -name __pycache__ -prune -exec rm -rf {} +
rm -rf build_web/app/caravana/README.md
cat > build_web/app/main.py <<'PY'
import asyncio

from caravana import ui
from caravana.app import App


async def main():
    ui.TOUCH = True  # en móvil/tablet: objetivos de toque grandes desde el primer fotograma
    await App().run_async()


asyncio.run(main())
PY
python -m pygbag --build build_web/app
echo "Listo: build_web/app/build/web (sube esa carpeta a cualquier hosting estático)"
