"""Build the GitHub Pages WASM site with all offline report assets."""
from pathlib import Path
import shutil
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'tools/prepare_reports.py'],cwd=root,check=True)
subprocess.run([sys.executable,'tools/compose_site.py'],cwd=root,check=True)
subprocess.run([sys.executable,'-m','marimo','check','lab01.py'],cwd=root,check=True)
subprocess.run([sys.executable,'-m','marimo','export','html-wasm','lab01.py','-o','site','--mode','run','--force'],cwd=root,check=True)
for folder in ['public','research']:
    shutil.copytree(root/folder,root/'site'/folder,dirs_exist_ok=True)
page=root/'site/index.html'
text=page.read_text(encoding="utf-8")
assert '</body>' in text
page.write_text(text.replace('<html lang="en">','<html lang="ru">',1),encoding='utf-8')
print('Built three reports. Frontend runtime is embedded as an anywidget for local and WASM use.')
