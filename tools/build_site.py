"""Сборка интерактивного сайта: python tools/build_site.py."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, '-m', 'marimo', 'export', 'html-wasm',
                'lab01.py', '-o', 'site', '--mode', 'run'], cwd=root, check=True)
print('Готово: site/index.html. Запуск: python -m http.server --directory site 8000')
