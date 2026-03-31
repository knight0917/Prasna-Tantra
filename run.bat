@echo off
setlocal enabledelayedexpansion

:: Force UTF-8 encoding for specialized TUI characters
SET PYTHONIOENCODING=utf-8

echo.
echo  =====================================================
echo    AstroTrack Python  ^|  Vedic Computation Engine
echo  =====================================================
echo.

:: ── 1. Python version guard (requires 3.10+) ──────────────────────────────
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and add it to PATH.
    pause & exit /b 1
)

FOR /F "tokens=2 delims= " %%V IN ('python --version 2^>^&1') DO SET PY_VER=%%V
FOR /F "tokens=1,2 delims=." %%A IN ("%PY_VER%") DO (
    SET PY_MAJOR=%%A
    SET PY_MINOR=%%B
)
IF %PY_MAJOR% LSS 3 (
    echo [ERROR] Python 3.10+ required. Found: %PY_VER%
    pause & exit /b 1
)
IF %PY_MAJOR% EQU 3 IF %PY_MINOR% LSS 10 (
    echo [ERROR] Python 3.10+ required. Found: %PY_VER%
    pause & exit /b 1
)
echo [OK] Python %PY_VER% detected.

:: ── 2. Virtual environment ─────────────────────────────────────────────────
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    IF ERRORLEVEL 1 (
        echo [ERROR] Failed to create virtual environment.
        pause & exit /b 1
    )
)
call venv\Scripts\activate.bat
echo [OK] Virtual environment active.

:: ── 3. Install / sync dependencies from requirements.txt ──────────────────
echo [INFO] Syncing dependencies from requirements.txt...
pip install -q -r requirements.txt streamlit geopy timezonefinder pytz
IF ERRORLEVEL 1 (
    echo [ERROR] Dependency installation failed. Check requirements.txt.
    pause & exit /b 1
)
echo [OK] Dependencies satisfied.

:: ── 4. First-run ephemeris notice ─────────────────────────────────────────
IF NOT EXIST "de421.bsp" (
    echo.
    echo [INFO] First run: downloading NASA JPL DE421 ephemeris ^(~17 MB^).
    echo        This happens once. Subsequent runs will use the cached file.
    echo.
)

:: ── 5. Mode Selection ─────────────────────────────────────────────────────
:: If user passes --ui, launch Streamlit. Otherwise launch standard CLI.

SET IS_UI=0
for %%x in (%*) do (
   if "%%x"=="--ui" set IS_UI=1
)

if %IS_UI%==1 (
    echo [INFO] Starting Prasna Tantra Dashboard (Streamlit)...
    echo.
    streamlit run app.py
) else (
    echo [INFO] Starting AstroTrack engine...
    echo  ───────────────────────────────────────────────────
    echo.
    python -m src.main %*
)

IF ERRORLEVEL 1 (
    echo.
    echo [ERROR] Application exited with an error.
    pause & exit /b 1
)

:: ── 6. Done ───────────────────────────────────────────────────────────────
echo.
echo  =====================================================
echo  [SUCCESS] Session complete.
echo  =====================================================
pause
