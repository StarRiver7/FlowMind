@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title FlowMind - Start All Services

:: ============================================================
:: FlowMind - Windows Dev Environment One-Click Start
:: ============================================================

set "ROOT=%~dp0.."
pushd "%ROOT%"
set "ROOT=%CD%"
popd

:: === User Configuration (edit if yours differs) ===
set "NODE_HOME=F:\node22\node-v22.14.0-win-x64"
set "CONDA_ENV=flowmind"

:: === Service Port Map ===
set "MYSQL_PORT=3306"
set "REDIS_PORT=6379"
set "JAVA_PORT=8080"
set "AI_PORT=8000"
set "FRONTEND_PORT=5173"

:: === Locate Conda activate script ===
set "CONDA_ACTIVATE="
if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
    set "CONDA_ACTIVATE=%USERPROFILE%\miniconda3\Scripts\activate.bat"
) else if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
    set "CONDA_ACTIVATE=%USERPROFILE%\anaconda3\Scripts\activate.bat"
) else if exist "%USERPROFILE%\AppData\Local\miniconda3\Scripts\activate.bat" (
    set "CONDA_ACTIVATE=%USERPROFILE%\AppData\Local\miniconda3\Scripts\activate.bat"
) else if exist "%ALLUSERSPROFILE%\miniconda3\Scripts\activate.bat" (
    set "CONDA_ACTIVATE=%ALLUSERSPROFILE%\miniconda3\Scripts\activate.bat"
)

echo.
echo   ============================================
echo     FlowMind Dev Environment Starting ...
echo   ============================================
echo.
echo   Project:  %ROOT%
echo   Node.js:  %NODE_HOME%
echo   Conda:    %CONDA_ENV%
if defined CONDA_ACTIVATE echo   Conda at: %CONDA_ACTIVATE%
echo.

:: ============================================================
:: 1. Port Conflict Detection
:: ============================================================
echo [1/6] Checking port availability...

set "PORT_CONFLICT=0"
for %%P in (%MYSQL_PORT% %REDIS_PORT% %JAVA_PORT% %AI_PORT% %FRONTEND_PORT%) do (
    netstat -ano | findstr ":%%P " | findstr "LISTENING" >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING"') do (
            echo   [WARN] Port %%P in use by PID=%%A, attempting release...
            taskkill /PID %%A /F >nul 2>&1
            if !errorlevel! equ 0 (
                echo   [OK] Released port %%P
            ) else (
                echo   [FAIL] Cannot release port %%P
                set "PORT_CONFLICT=1"
            )
        )
    ) else (
        echo   [OK] Port %%P available
    )
)

if !PORT_CONFLICT! equ 1 (
    echo.
    echo   ============================================
    echo     PORT CONFLICT - resolve and retry
    echo   ============================================
    pause
    exit /b 1
)

:: ============================================================
:: 2. Runtime Check
:: ============================================================
echo.
echo [2/6] Checking runtime dependencies...

:: Node.js
if exist "%NODE_HOME%\node.exe" (
    for /f "tokens=*" %%i in ('"%NODE_HOME%\node.exe" -v') do echo   [OK] Node.js %%i
) else (
    echo   [WARN] Node.js not found at %NODE_HOME%
    where node >nul 2>&1 || (echo   [FAIL] Node.js not found & pause & exit /b 1)
    for /f "tokens=*" %%i in ('node -v') do echo   [OK] Node.js %%i ^(fallback^)
)

:: pnpm
where pnpm >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%NODE_HOME%\pnpm.cmd" (
        echo   [OK] pnpm ^(%%NODE_HOME%%^)
    ) else (
        echo   [FAIL] pnpm not found - run: npm install -g pnpm
        pause & exit /b 1
    )
) else (
    for /f "tokens=*" %%i in ('pnpm -v') do echo   [OK] pnpm %%i
)

:: Java
where java >nul 2>&1 || (echo   [FAIL] Java not found & pause & exit /b 1)
for /f "tokens=*" %%i in ('java -version 2^>^&1 ^| findstr /i "version"') do echo   [OK] Java %%i

:: Conda
if not defined CONDA_ACTIVATE (
    echo   [WARN] Conda activate.bat not found at common paths
    echo          If you have conda, edit CONDA_ACTIVATE in this script
) else (
    echo   [OK] Conda found
)

:: Maven
if exist "%ROOT%\java-service\mvnw.cmd" (
    set "MVN_CMD=%ROOT%\java-service\mvnw.cmd"
    echo   [OK] Maven Wrapper
) else (
    where mvn >nul 2>&1 && (set "MVN_CMD=mvn" & echo   [OK] Maven) || echo   [WARN] Maven not found - Java will be skipped
)

echo   [INFO] Ensure MySQL is running on port %MYSQL_PORT%
echo   [INFO] Ensure Redis is running on port %REDIS_PORT%

:: ============================================================
:: 3. Frontend Dependencies
:: ============================================================
echo.
echo [3/6] Checking frontend dependencies...

if not exist "%ROOT%\frontend\node_modules" (
    echo   Installing (pnpm install)...
    pushd "%ROOT%\frontend"
    call pnpm install
    popd
    echo   [OK] Done
) else (
    echo   [OK] Already installed
)

:: ============================================================
:: 4. Conda Environment & Python Deps
:: ============================================================
echo.
echo [4/6] Setting up Conda environment...

:: Init conda in this shell
if defined CONDA_ACTIVATE call "%CONDA_ACTIVATE%" >nul 2>&1

:: Check/create conda env
conda env list 2>nul | findstr /i "%CONDA_ENV%" >nul 2>&1
if %errorlevel% neq 0 (
    echo   Creating conda env '%CONDA_ENV%'...
    conda create -n %CONDA_ENV% python=3.11 -y
    echo   [OK] Created
) else (
    echo   [OK] Conda env '%CONDA_ENV%' exists
)

:: Install/update Python deps
echo   Installing Python dependencies...
call conda activate %CONDA_ENV%
pushd "%ROOT%\python-ai-service"
pip install -r requirements.txt -q 2>&1
popd
echo   [OK] Python dependencies ready

:: ============================================================
:: 5. Log Directory
:: ============================================================
echo.
echo [5/6] Creating log directory...

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"
echo   [OK] %ROOT%\logs

:: ============================================================
:: 6. Launch All Services
:: ============================================================
echo.
echo [6/6] Launching services...
echo.
echo   ============================================
echo     Services launch in separate windows
echo     Keep this window open
echo   ============================================
echo.

:: Build a conda init snippet for child windows
set "CONDA_INIT="
if defined CONDA_ACTIVATE set "CONDA_INIT=call "%CONDA_ACTIVATE%" >nul 2>&1 && "

:: --- A. Frontend (Element Plus, Vite HMR) ---
echo   Launching Frontend [:%FRONTEND_PORT%]
start "FlowMind-Frontend" cmd /k ^
  "title FlowMind - Frontend :%FRONTEND_PORT% && ^
  set "PATH=%NODE_HOME%;%NODE_HOME%\node_modules\.bin;%%PATH%%" && ^
  cd /d "%ROOT%\frontend" && ^
  echo [%date% %time%] Frontend ^(Element Plus^) starting... && ^
  echo. && ^
  pnpm run dev:ele"

:: --- B. Python AI Service (uvicorn --reload, conda env) ---
echo   Launching Python AI [:%AI_PORT%]
start "FlowMind-AI" cmd /k ^
  "title FlowMind - Python AI :%AI_PORT% && ^
  %CONDA_INIT% ^
  conda activate %CONDA_ENV% && ^
  cd /d "%ROOT%\python-ai-service" && ^
  echo [%date% %time%] Python AI starting... && ^
  echo. && ^
  uvicorn app.main:app --reload --host 0.0.0.0 --port %AI_PORT%"

:: --- C. Java Backend (Spring Boot DevTools) ---
if defined MVN_CMD (
    echo   Launching Java Backend [:%JAVA_PORT%]
    start "FlowMind-Java" cmd /k ^
      "title FlowMind - Java :%JAVA_PORT% && ^
      cd /d "%ROOT%\java-service" && ^
      echo [%date% %time%] Java backend starting... && ^
      echo. && ^
      "%MVN_CMD%" spring-boot:run -Dspring-boot.run.profiles=dev -DskipTests"
) else (
    echo   [SKIP] Java ^(Maven not found^)
)

:: ============================================================
:: Wait & Open Browser
:: ============================================================
echo.
echo   Waiting for services...

echo   - Frontend (%FRONTEND_PORT%)...
call :wait_for_port %FRONTEND_PORT% 30 "Frontend"

echo   - Python AI (8000)...
call :wait_for_port %AI_PORT% 30 "Python AI"

if defined MVN_CMD (
    echo   - Java (8080)...
    call :wait_for_port %JAVA_PORT% 90 "Java Backend"
)

echo.
echo   ============================================
echo     All services are up!
echo   ============================================
echo.
echo   Frontend:   http://localhost:%FRONTEND_PORT%
echo   AI Docs:    http://localhost:%AI_PORT%/docs
echo   Java API:   http://localhost:%JAVA_PORT%/swagger-ui.html
echo   Health:     http://localhost:%AI_PORT%/health
echo.

start http://localhost:%FRONTEND_PORT%

echo   Close individual service windows to stop.
echo   Press any key to close this launcher...
pause >nul
exit /b 0

:: ============================================================
:: Helper: wait for port LISTENING
:: ============================================================
:wait_for_port
set "port=%~1"
set "timeout=%~2"
set "name=%~3"
set "elapsed=0"

:wait_loop
timeout /t 2 /nobreak >nul
set /a elapsed+=2
netstat -ano | findstr ":%port% " | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo     [OK] %name% ready ^(!elapsed!s^)
    exit /b 0
)
if !elapsed! geq %timeout% (
    echo     [WARN] %name% timeout ^(>%timeout%s^)
    exit /b 0
)
goto wait_loop
