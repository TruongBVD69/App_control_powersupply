@echo off
REM Thư mục chứa code
set SOURCE_DIR=sources
set ASSETS_DIR=assets
set MAIN_PY=%SOURCE_DIR%\main.py
set ICON_PATH=%ASSETS_DIR%\myicon.ico

REM Xoá thư mục build cũ
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo ============================================
echo   Bat dau build ung dung Python bang PyInstaller
echo ============================================

pyinstaller --onefile --windowed --icon=%ICON_PATH% %MAIN_PY%

if %ERRORLEVEL%==0 (
    echo --------------------------------------------
    echo Build thanh cong! File exe nam trong thu muc dist
    echo --------------------------------------------
) else (
    echo --------------------------------------------
    echo Build that bai! Kiem tra lai loi tren console
    echo --------------------------------------------
)

pause
