@echo off
echo AI Trend Navigator - Daily Supabase Update
echo ==========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if exist "venv\" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found
    echo Please run setup_supabase.py first to create configuration
    pause
    exit /b 1
)

REM Ask user for update mode
echo Choose update mode:
echo 1. Incremental Update (default - only add missing data)
echo 2. Force Refresh (clear all data and re-insert everything)
echo 3. Process specific timeframe only
echo.
set /p choice="Enter your choice (1-3, or press Enter for default): "

REM Set default choice
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo Running incremental update (will skip existing data)...
    python daily_supabase_update.py
) else if "%choice%"=="2" (
    echo.
    echo Running force refresh (will clear and re-insert all data)...
    python daily_supabase_update.py --force-refresh
) else if "%choice%"=="3" (
    echo.
    echo Available timeframes: 4H, 8H, 1D, 1W, 1M
    set /p timeframe="Enter timeframe: "
    echo.
    echo Running update for %timeframe% timeframe only...
    python daily_supabase_update.py --timeframe %timeframe%
) else (
    echo Invalid choice. Running default incremental update...
    python daily_supabase_update.py
)

REM Check if script ran successfully
if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: Daily update completed successfully!
) else (
    echo.
    echo ERROR: Daily update failed with error code %errorlevel%
)

echo.
echo Press any key to exit...
pause >nul 