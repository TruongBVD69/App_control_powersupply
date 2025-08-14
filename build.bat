@echo off
REM ================================
REM Configuration for building Python application
REM This script uses PyInstaller to create a standalone executable
REM ================================
set SOURCE_DIR=sources
set ASSETS_DIR=assets
set MAIN_PY=%SOURCE_DIR%\main.py
set ICON_PATH=%ASSETS_DIR%\myicon.ico
set OUTPUT_DIR=Output
set APP_NAME=PowerSupply Controller

REM ================================
REM Delete old build directories if they exist
REM ================================
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM ================================
REM Prompt for application version
REM This will be used in the version.txt file
REM ================================
set /p APP_VERSION=Enter the application version (e.g., 1.0.0): 

REM ================================
REM Create output directory if it doesn't exist
REM ================================
if not exist %OUTPUT_DIR% mkdir %OUTPUT_DIR%

(
    echo AppName: %APP_NAME%
    echo Version: %APP_VERSION%
    echo BuildTime: %date% %time%
) > %OUTPUT_DIR%\version.txt

echo --------------------------------------------
echo Created version.txt file at %OUTPUT_DIR%\version.txt with version v%APP_VERSION%
echo --------------------------------------------

REM ================================
REM Check and install required Python modules
REM ================================
echo Checking required Python modules...

call :CheckAndInstallModule pyserial serial
call :CheckAndInstallModule requests
call :CheckAndInstallModule PyInstaller
call :CheckAndInstallModule pyaudio
@REM call :CheckAndInstallModule SpeechRecognition
@REM call :CheckAndInstallModule pywin32
REM You can add more modules as needed
REM call :CheckAndInstallModule requests
REM call :CheckAndInstallModule some_other_module

goto BuildApp

:CheckAndInstallModule
    set MODULE_NAME=%1
    set IMPORT_NAME=%2
    if "%IMPORT_NAME%"=="" set IMPORT_NAME=%MODULE_NAME%

    echo.
    echo Checking module "%MODULE_NAME%"...
    python -c "import %IMPORT_NAME%" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Module "%MODULE_NAME%" not found. Installing...
        pip install %MODULE_NAME%
        if %ERRORLEVEL% NEQ 0 (
            echo Failed to install %MODULE_NAME%! Please install manually and try again.
            pause
            exit /b 1
        ) else (
            echo Successfully installed %MODULE_NAME%.
        )
    ) else (
        echo Module "%MODULE_NAME%" is already installed.
    )
    exit /b 0

REM ================================
REM Build the application
REM ================================
:BuildApp
echo ============================================
echo Start building Python application using PyInstaller
echo ============================================

REM Build main.py
python -m PyInstaller --noconfirm --onedir --windowed --icon=%ICON_PATH% %MAIN_PY%

REM Build voice_app.py (giữ icon hoặc đổi icon khác nếu cần)
python -m PyInstaller --noconfirm --onedir --windowed  sources\voice_app.py

if %ERRORLEVEL%==0 (
    echo --------------------------------------------
    echo Build successful! Executable created in the dist directory.
    echo --------------------------------------------
) else (
    echo --------------------------------------------
    echo Build failed! Please check the error messages above.
    echo --------------------------------------------
)

pause
exit /b 0
