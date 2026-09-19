@echo off
title SwiftPOS Windows Executable Builder
echo ========================================================
echo   SwiftPOS - Standalone Windows Executable Builder
echo ========================================================
echo.

python build_exe.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build encountered an error.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [DONE] SwiftPOS.exe is ready in the 'dist' folder!
pause
