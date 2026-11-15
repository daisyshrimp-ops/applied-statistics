"""Open the normal marimo app; reading animations are built into its widget."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-m','pip','install','-r','requirements.txt'],cwd=root,check=True)
subprocess.run([sys.executable,'tools/prepare_reports.py'],cwd=root,check=True)
subprocess.run([sys.executable,'tools/compose_site.py'],cwd=root,check=True)
subprocess.run([sys.executable,'-m','marimo','run','lab01.py'],cwd=root,check=True)
