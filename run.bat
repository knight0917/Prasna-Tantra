@echo off
echo =========================================
echo       AstroTrack Physics Engine          
echo =========================================
echo.

:: Check if virtual environment exists
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [INFO] Virtual environment not found. Creating one now...
    python -m venv venv
)

:: Activate the environment
call venv\Scripts\activate.bat

:: Silently ensure dependencies are satisfied
echo [INFO] Verifying physics dependencies...
pip install -q skyfield pydantic geopy timezonefinder pytz

echo [INFO] Executing Core Engine Benchmark...
echo.
python -m src.main

echo.
echo =========================================
echo [SUCCESS] Execution Complete.
pause
