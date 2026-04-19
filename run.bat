@echo off
setlocal

cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

set "VENV_PY=venv\Scripts\python.exe"
set "VENV_PIP=venv\Scripts\pip.exe"

echo.
echo ==========================================
echo   Prasna Tantra Launcher
echo ==========================================
echo.

if not exist "%VENV_PY%" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
)

echo [INFO] Installing dependencies...
"%VENV_PIP%" install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    exit /b 1
)

set "MODE=ui"
for %%x in (%*) do (
    if /I "%%x"=="--ui" set "MODE=ui"
    if /I "%%x"=="--cli" set "MODE=cli"
)

if /I "%MODE%"=="cli" (
    echo [INFO] Starting Prasna CLI...
    "%VENV_PY%" -m src.main --prasna
) else (
    echo [INFO] Starting Streamlit UI...
    "%VENV_PY%" -m streamlit run app.py
)
