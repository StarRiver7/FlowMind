@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title FlowMind — Stop All Services

:: ============================================================
:: FlowMind — Stop all running services by port
:: ============================================================

echo.
echo   ============================================
echo     FlowMind — Stopping all services ...
echo   ============================================
echo.

:: === Service Port Map ===
set "JAVA_PORT=8080"
set "AI_PORT=8000"
set "FRONTEND_PORT=5173"
set "GRPC_PORT=9090"

set "KILLED=0"
set "NOT_FOUND=0"

for %%P in (%FRONTEND_PORT% %AI_PORT% %JAVA_PORT% %GRPC_PORT%) do (
    set "found=0"
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING" 2^>nul') do (
        set "pid=%%A"
        if not "!pid!"=="" (
            set "found=1"
            echo   Killing PID !pid! on port %%P ...
            taskkill /PID !pid! /F >nul 2>&1
            if !errorlevel! equ 0 (
                echo   [OK] Stopped process on port %%P (PID !pid!)
                set /a KILLED+=1
            ) else (
                echo   [FAIL] Could not kill PID !pid! on port %%P
            )
        )
    )
    if "!found!"=="0" (
        echo   [N/A] No process found on port %%P
        set /a NOT_FOUND+=1
    )
)

echo.
echo   ============================================
echo     Stopped: %KILLED% process(es)
echo     Already stopped: %NOT_FOUND%
echo   ============================================
echo.

:: Also close any lingering Java/Maven processes by name (optional safety net)
taskkill /FI "WINDOWTITLE eq FlowMind*" /F >nul 2>&1

echo   Done! Press any key to close...
pause >nul
exit /b 0
