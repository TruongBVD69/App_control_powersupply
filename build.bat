@echo off
REM ================================
REM Cấu hình thư mục và file
REM ================================
set SOURCE_DIR=sources
set ASSETS_DIR=assets
set MAIN_PY=%SOURCE_DIR%\main.py
set ICON_PATH=%ASSETS_DIR%\myicon.ico
set OUTPUT_DIR=Output

REM ================================
REM Xoá thư mục build cũ
REM ================================
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM ================================
REM Nhập phiên bản mới để build
REM ================================
set /p APP_VERSION=Nhập số phiên bản (vd: 1.0.3): 

REM ================================
REM Tạo thư mục Output nếu chưa có
REM ================================
if not exist %OUTPUT_DIR% mkdir %OUTPUT_DIR%

set APP_NAME=My GPP-3323 Controller

(
    echo AppName: %APP_NAME%
    echo Version: v%APP_VERSION%
    echo BuildTime: %date% %time%
) > %OUTPUT_DIR%\version.txt

echo --------------------------------------------
echo Đã tạo file version.txt tại %OUTPUT_DIR%\version.txt với version v%APP_VERSION%
echo --------------------------------------------

REM ================================
REM Build ứng dụng Python
REM ================================
echo ============================================
echo   Bắt đầu build ứng dụng Python bằng PyInstaller
echo ============================================

pyinstaller --onefile --windowed --icon=%ICON_PATH% %MAIN_PY%

if %ERRORLEVEL%==0 (
    echo --------------------------------------------
    echo Build thành công! File exe nằm trong thư mục dist
    echo --------------------------------------------
) else (
    echo --------------------------------------------
    echo Build thất bại! Kiểm tra lại lỗi trên console
    echo --------------------------------------------
)

pause
