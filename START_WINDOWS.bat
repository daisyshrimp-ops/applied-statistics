@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"
if exist ".venv312\Scripts\python.exe" (
 ".venv312\Scripts\python.exe" tools/serve_site.py
 goto end
)
if exist ".venv\Scripts\python.exe" (
 ".venv\Scripts\python.exe" tools/serve_site.py
 goto end
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
 "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m venv .venv312
 if errorlevel 1 goto failed
 ".venv312\Scripts\python.exe" -m pip install -r requirements.txt
 if errorlevel 1 goto failed
 ".venv312\Scripts\python.exe" tools/serve_site.py
 goto end
)
echo Open README.md: install Python and create the project environment.
goto failed
:failed
pause
exit /b 1
:end
if errorlevel 1 goto failed
