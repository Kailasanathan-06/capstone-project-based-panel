@echo off
echo Building MEC Agent executable...

REM Install PyInstaller if not present
pip install pyinstaller --quiet

REM Build the executable
pyinstaller --clean mec_agent.spec

REM Copy to release folder
if exist dist\MEC_Agent.exe (
    mkdir release 2>nul
    copy dist\MEC_Agent.exe release\MEC_Agent.exe
    echo.
    echo ========================================
    echo Build successful!
    echo Executable: release\MEC_Agent.exe
    echo ========================================
) else (
    echo.
    echo Build failed!
    exit /b 1
)