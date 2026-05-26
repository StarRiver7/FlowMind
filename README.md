# FlowMind - Enterprise AI Agent Platform

Multi-service AI agent orchestration platform with RAG pipeline, LLM integration, and workflow automation.

## Architecture

```
FlowMind/
├── frontend/           Vue Vben Admin (Element Plus) - port 5173
├── java-service/       Spring Boot 3 + MyBatis Plus - port 8080
├── python-ai-service/  FastAPI + LangChain + LangGraph - port 8000
├── sql/                Flyway migrations (MySQL)
└── scripts/            Windows dev tooling
```

### Infrastructure

| Service | Port | Notes |
|---------|------|-------|
| MySQL   | 3306 | Windows Service |
| Redis   | 6379 | Windows Service |
| Milvus  | *(embedded)* | Runs in-process in Python AI |

## Quick Start (Windows)

```bat
:: 1. Check prerequisites
scripts\check-env.bat

:: 2. One-click start all services
scripts\start-all.bat

:: 3. Stop everything
scripts\stop-all.bat
```

### What `start-all.bat` does

1. Detects port conflicts, auto-releases occupied ports
2. Checks Node.js (`F:\node22\`), pnpm, Java, Conda
3. Creates Conda env `flowmind` if missing
4. Installs Python dependencies via pip
5. Launches 3 services in separate `cmd` windows
6. Waits for each to be ready, then opens the browser

### Service Windows

| Window Title               | Command                          |
|----------------------------|----------------------------------|
| `FlowMind - Frontend :5173` | `pnpm run dev:ele` (Element Plus) |
| `FlowMind - Python AI :8000` | `uvicorn app.main:app --reload`  |
| `FlowMind - Java :8080`     | `mvnw spring-boot:run`           |

## Manual Start

### 1. Infrastructure

Ensure MySQL and Redis are running as Windows services.

### 2. Frontend (Element Plus)

```powershell
cd frontend
$env:Path = "F:\node22\node-v22.14.0-win-x64;" + $env:Path
pnpm install        # first run only
pnpm run dev:ele    # Vite HMR on port 5173
```

### 3. Python AI Service

```powershell
cd python-ai-service
conda activate flowmind
pip install -r requirements.txt   # first run only
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Java Backend

```bash
cd java-service
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev
```

## Service URLs

| Service      | URL                                   |
|-------------|---------------------------------------|
| Frontend     | http://localhost:5173                 |
| AI API Docs  | http://localhost:8000/docs            |
| AI Health    | http://localhost:8000/health          |
| Java API     | http://localhost:8080                 |
| Swagger UI   | http://localhost:8080/swagger-ui.html |
| Actuator     | http://localhost:8080/actuator/health |

## Hot Reload

| Service  | Mechanism              |
|----------|------------------------|
| Frontend | Vite HMR (instant)     |
| Python   | uvicorn `--reload`     |
| Java     | Spring Boot DevTools   |

## Configuration

### Dev Credentials (default)

| Service | User | Password |
|---------|------|----------|
| MySQL   | root | 123456   |
| Redis   | *(none)* |      |

### Key files

| File | Purpose |
|------|---------|
| `.env` at root | Infrastructure credentials |
| `python-ai-service/.env` | LLM keys, Milvus path, RAG settings |
| `java-service/src/main/resources/application-dev.yml` | Java dev profile |

Copy `.env.example` to `.env` files and fill in API keys.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/check-env.bat` | Check Node/Conda/Java/ports |
| `scripts/start-all.bat` | One-click launch all services |
| `scripts/stop-all.bat`  | Kill all by port |

## Customization

Edit these lines near the top of `start-all.bat` if your paths differ:

```bat
:: Your Node.js installation path
set "NODE_HOME=F:\node22\node-v22.14.0-win-x64"

:: Your Conda environment name for this project
set "CONDA_ENV=flowmind"
```

## Troubleshooting

**Port already in use** — Run `scripts/stop-all.bat` first.

**Conda not found** — The script auto-detects Miniconda at common paths. If yours is elsewhere, run `conda init cmd.exe` once.

**pnpm not found** — Install globally: `npm install -g pnpm` or ensure `%NODE_HOME%\pnpm.cmd` exists.

**MySQL connection refused** — Start MySQL service: `net start MySQL80` (or your service name).
