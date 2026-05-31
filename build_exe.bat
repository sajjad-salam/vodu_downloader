@echo off
REM Build script for Vodu Downloader executable
REM This script creates a standalone .exe file

echo ========================================
echo Vodu Downloader - Build Executable
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller. Please run: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo.
echo Building executable with PyInstaller...
echo.

REM Build the executable
pyinstaller --clean main.spec

if errorlevel 1 (
    echo.
    echo Build failed! Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build successful!
echo ========================================
echo.
echo Your executable is located in: dist\VoduDownloader.exe
echo.
pause
