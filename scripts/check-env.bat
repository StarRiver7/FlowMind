@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title FlowMind - Environment Check

:: ============================================================
:: FlowMind - Check development environment prerequisites
:: ============================================================

set "NODE_HOME=F:\node22\node-v22.14.0-win-x64"
set "CONDA_ENV=flowmind"

echo.
echo   ============================================
echo     FlowMind - Environment Check
echo   ============================================
echo.

set "ALL_OK=1"

:: --- OS ---
echo   [OS]
for /f "tokens=2 delims=[]" %%i in ('ver') do echo     Windows %%i

:: --- Node.js ---
echo.
echo   [Node.js]
if exist "%NODE_HOME%\node.exe" (
    for /f "tokens=*" %%i in ('"%NODE_HOME%\node.exe" -v') do echo     %%i ^(from %NODE_HOME%^)
) else (
    where node >nul 2>&1
    if %errorlevel% neq 0 (
        echo     [MISSING] Node.js - install v18+
        set "ALL_OK=0"
    ) else (
        for /f "tokens=*" %%i in ('node -v') do echo     %%i ^(PATH fallback^)
    )
)

:: --- pnpm ---
echo   [pnpm]
where pnpm >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%NODE_HOME%\pnpm.cmd" (
        echo     %%NODE_HOME%%\pnpm.cmd found
    ) else (
        echo     [MISSING] pnpm - run: npm install -g pnpm
        set "ALL_OK=0"
    )
) else (
    for /f "tokens=*" %%i in ('pnpm -v') do echo     pnpm %%i
)

:: --- Java ---
echo.
echo   [Java]
where java >nul 2>&1
if %errorlevel% neq 0 (
    echo     [MISSING] Java - install JDK 17+
    set "ALL_OK=0"
) else (
    for /f "tokens=*" %%i in ('java -version 2^>^&1 ^| findstr /i "version"') do echo     %%i
)

:: --- Maven ---
echo   [Maven]
if exist "%~dp0..\java-service\mvnw.cmd" (
    echo     Maven Wrapper ready
) else (
    where mvn >nul 2>&1
    if %errorlevel% neq 0 (
        echo     [MISSING] Maven
    ) else (
        for /f "tokens=*" %%i in ('mvn -version 2^>^&1 ^| findstr /i "Apache Maven"') do echo     %%i
    )
)

:: --- Conda ---
echo.
echo   [Conda]
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo     [MISSING] Conda - install Miniconda
    set "ALL_OK=0"
) else (
    for /f "tokens=1,2" %%i in ('conda --version') do echo     conda %%i %%j
    echo   [Conda env: %CONDA_ENV%]
    conda env list | findstr /i "%CONDA_ENV%" >nul 2>&1
    if %errorlevel% neq 0 (
        echo     [MISSING] Conda env '%CONDA_ENV%' not found
    ) else (
        echo     [OK] Conda env '%CONDA_ENV%' exists
    )
)

:: --- MySQL ---
echo.
echo   [MySQL - port 3306]
netstat -ano | findstr ":3306 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% neq 0 (
    echo     [NOT RUNNING] Start MySQL service
) else (
    echo     [OK] MySQL listening on 3306
)

:: --- Redis ---
echo   [Redis - port 6379]
netstat -ano | findstr ":6379 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% neq 0 (
    echo     [NOT RUNNING] Start Redis service
) else (
    echo     [OK] Redis listening on 6379
)

:: --- Ports ---
echo.
echo   [Port Availability]
for %%P in (8080 8000 5777) do (
    netstat -ano | findstr ":%%P " | findstr "LISTENING" >nul 2>&1
    if !errorlevel! equ 0 (
        echo     Port %%P: IN USE
    ) else (
        echo     Port %%P: available
    )
)

:: --- Summary ---
echo.
echo   ============================================
if %ALL_OK% equ 1 (
    echo     All runtimes OK! Ready to start.
) else (
    echo     Some prerequisites missing. Fix above.
)
echo   ============================================
echo.

pause
exit /b 0

