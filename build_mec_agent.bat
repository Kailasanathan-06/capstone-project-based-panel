@echo off
setlocal
title SecureDT - Build MEC Agent

set "SERVER_URL=http://127.0.0.1:8000"

echo ============================================================
echo  SecureDT - MEC Agent Build + Cloud Connection Check
echo ============================================================
echo.

echo [1/3] Checking cloud server at %SERVER_URL% ...
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%SERVER_URL%/api/cloud/status/' -UseBasicParsing -TimeoutSec 8; $j = $r.Content | ConvertFrom-Json; Write-Host ('  Cloud API OK - mode=' + $j.mode + ', configured=' + $j.configured + ', files=' + $j.total_files) } catch { Write-Host '  Cloud API unreachable - start it with: python manage.py runserver 0.0.0.0:8000' }"

echo.
echo [2/3] Checking MEC gateway communication ...
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%SERVER_URL%/api/mec/connected/' -UseBasicParsing -TimeoutSec 8; $j = $r.Content | ConvertFrom-Json; Write-Host ('  MEC gateway connected=' + $j.connected + ', device=' + $j.device_id) } catch { Write-Host '  MEC gateway unreachable - check MEC-001 registration' }"

echo.
echo [3/3] Building MEC Agent executable ...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo  Failed to install PyInstaller
    exit /b 1
)

pyinstaller --clean mec_agent.spec
if errorlevel 1 (
    echo  Build failed during PyInstaller compilation
    exit /b 1
)

if not exist "dist\MEC_Agent.exe" (
    echo  Build failed - dist\MEC_Agent.exe was not created
    exit /b 1
)

if not exist "release" mkdir "release"
copy /Y "dist\MEC_Agent.exe" "release\MEC_Agent.exe" >nul

echo.
echo ============================================================
echo  Build successful!
echo  Executable: release\MEC_Agent.exe
echo ============================================================
exit /b 0
