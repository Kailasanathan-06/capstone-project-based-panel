@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SecureDT - Launcher

set "HOST=0.0.0.0"
set "PORT=%SECUREDT_PORT%"
if not defined PORT set "PORT=8000"
set "NO_BROWSER=%SECUREDT_NO_BROWSER%"
set "CHECK_ONLY="
set "BUILD_AGENT="

:PARSE_ARGS
if "%~1"=="" goto PARSE_DONE
if /i "%~1"=="--check" set "CHECK_ONLY=1"
if /i "%~1"=="--no-browser" set "NO_BROWSER=1"
if /i "%~1"=="build" set "BUILD_AGENT=1"
if /i "%~1"=="--build" set "BUILD_AGENT=1"
echo(%~1|findstr /r "^[0-9][0-9]*$" >nul
if not errorlevel 1 set "PORT=%~1"
shift
goto PARSE_ARGS
:PARSE_DONE

echo ============================================================
echo  SecureDT - Unified Launcher
echo ============================================================
if defined BUILD_AGENT (
    echo  Mode    : Build MEC Agent executable
) else (
    echo  Mode    : Start SecureDT server
    echo  Frontend: http://127.0.0.1:%PORT%/
    echo  APIs    : http://127.0.0.1:%PORT%/api/
)
echo.

set "PYEXE="
where py >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PYEXE=%%P"
)
if not defined PYEXE (
    for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYEXE=%%P"
)
if not defined PYEXE (
    echo [ERROR] Python 3 was not found. Install Python 3.11+ and re-run.
    pause
    exit /b 1
)
echo  Python  : %PYEXE%
echo.

if defined BUILD_AGENT goto BUILD_MEC_AGENT

echo [1/5] Checking Python environment...
"%PYEXE%" -c "import django, rest_framework, corsheaders, dotenv, psutil, requests, pandas, numpy" >nul 2>&1
if not errorlevel 1 goto ENV_READY

echo       Core packages are missing. Preparing local virtual environment...
if not exist "%~dp0venv\Scripts\python.exe" (
    echo       Creating venv...
    "%PYEXE%" -m venv "%~dp0venv"
    if errorlevel 1 (
        echo [ERROR] Failed to create the virtual environment.
        pause
        exit /b 1
    )
)
set "PYEXE=%~dp0venv\Scripts\python.exe"

echo       Upgrading pip...
"%PYEXE%" -m pip install --upgrade pip --quiet
if errorlevel 1 echo       [WARN] pip upgrade failed; continuing.

echo       Installing requirements.txt...
"%PYEXE%" -m pip install -r requirements.txt
if not errorlevel 1 goto DEPS_READY

echo       [WARN] Full install failed; retrying without mysqlclient (SQLite mode)...
powershell -NoProfile -Command "$lines = Get-Content -LiteralPath 'requirements.txt' | Where-Object { $_ -notmatch '^\s*mysqlclient' }; Set-Content -LiteralPath '%TEMP%\secure_dt_requirements_sqlite.txt' -Value $lines -Encoding UTF8"
"%PYEXE%" -m pip install -r "%TEMP%\secure_dt_requirements_sqlite.txt"
if errorlevel 1 (
    echo [ERROR] Dependency installation failed. Check your internet connection and Python version.
    pause
    exit /b 1
)

:DEPS_READY
"%PYEXE%" -c "import django, rest_framework, corsheaders, dotenv, psutil, requests, pandas, numpy" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Required packages are still unavailable after installation.
    pause
    exit /b 1
)

:ENV_READY
echo       Python environment ready.

echo [2/5] Running Django system checks...
"%PYEXE%" manage.py check
if errorlevel 1 (
    echo [ERROR] Django system check failed.
    pause
    exit /b 1
)

echo [3/5] Applying database migrations...
"%PYEXE%" manage.py migrate --noinput
if errorlevel 1 (
    echo [ERROR] Database migration failed.
    pause
    exit /b 1
)

echo [4/5] Initializing local, MEC, and cloud storage tiers...
"%PYEXE%" manage.py shell -c "from engine.storage_manager import ensure_storage_destinations_initialized; ensure_storage_destinations_initialized(); print('Storage tiers ready')"
if errorlevel 1 (
    echo [ERROR] Storage tier initialization failed.
    pause
    exit /b 1
)

if /i "%SECUREDT_COLLECTSTATIC%"=="1" (
    echo       Collecting static files...
    "%PYEXE%" manage.py collectstatic --noinput
    if errorlevel 1 echo       [WARN] collectstatic failed; DEBUG mode can still serve static files.
)

if defined CHECK_ONLY (
    echo.
    echo [OK] Setup check complete. Server was not started.
    exit /b 0
)

echo [5/5] Starting server (frontend + backend + APIs)...
netstat -ano | findstr ":%PORT% " >nul
if not errorlevel 1 (
    echo       [WARN] Port %PORT% looks busy. Try: run.bat 8001
)

if not defined NO_BROWSER (
    start "" powershell -NoProfile -Command "Start-Sleep -Seconds 4; Start-Process 'http://127.0.0.1:%PORT%/'"
)

echo.
echo  Press CTRL+C to stop the SecureDT server.
echo.
set "PYTHONUNBUFFERED=1"
"%PYEXE%" manage.py runserver %HOST%:%PORT%
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo  SecureDT server stopped with exit code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%

:BUILD_MEC_AGENT
echo [1/3] Checking cloud server at http://127.0.0.1:%PORT% ...
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:%PORT%/api/cloud/status/' -UseBasicParsing -TimeoutSec 8; $j = $r.Content | ConvertFrom-Json; Write-Host ('  Cloud API OK - mode=' + $j.mode + ', configured=' + $j.configured + ', files=' + $j.total_files) } catch { Write-Host '  Cloud API unreachable - start the server with: run.bat' }"

echo.
echo [2/3] Checking MEC gateway communication ...
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:%PORT%/api/mec/connected/' -UseBasicParsing -TimeoutSec 8; $j = $r.Content | ConvertFrom-Json; Write-Host ('  MEC gateway connected=' + $j.connected + ', device=' + $j.device_id) } catch { Write-Host '  MEC gateway unreachable - check MEC-001 registration' }"

echo.
echo [3/3] Building MEC Agent executable ...
"%PYEXE%" -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

"%PYEXE%" -m PyInstaller --clean mec_agent.spec
if errorlevel 1 (
    echo [ERROR] Build failed during PyInstaller compilation.
    pause
    exit /b 1
)

if not exist "dist\MEC_Agent.exe" (
    echo [ERROR] Build failed - dist\MEC_Agent.exe was not created.
    pause
    exit /b 1
)

if not exist "release" mkdir "release"
copy /Y "dist\MEC_Agent.exe" "release\MEC_Agent.exe" >nul

echo.
echo ============================================================
echo  Build complete: release\MEC_Agent.exe
echo ============================================================
exit /b 0
