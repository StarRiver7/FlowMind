# Enterprise AI Agent Platform

> 企业级 Java + Python AI Agent 混合架构平台

## 项目概述

本项目构建了一个生产级的多语言混合 Agent 平台，采用 **Java (Spring Boot)** 作为核心业务后端，**Python (FastAPI + LangChain)** 作为 AI 智能服务端。

### 架构职责划分

| 模块 | 技术栈 | 职责 |
|------|--------|------|
| `java-service` | Spring Boot 3.3, gRPC, Kafka, MySQL | 业务编排、事务控制、持久化、系统稳定性保障 |
| `python-ai-service` | FastAPI, LangChain, LangGraph | Prompt Engineering、LLM 推理、Agent 编排、非结构化分析 |
| `deploy` | Docker Compose, Kubernetes | 容器化部署、服务编排、环境一致性 |

### 通信机制

```
┌─────────────────┐         REST / gRPC        ┌──────────────────┐
│   java-service   │◄──────────────────────────►│ python-ai-service │
│   (Core Backend) │                             │   (AI Service)   │
│   Port: 8080     │         Kafka Event         │   Port: 8000     │
│   gRPC: 9090     │◄──────────────────────────►│   gRPC: 50051    │
└────────┬────────┘                             └──────────────────┘
         │
    ┌────┴────┐
    │  MySQL   │
    │  Redis   │
    └─────────┘
```

## 快速开始

### 环境要求

- JDK 21+
- Python 3.11+
- Docker & Docker Compose
- Maven 3.9+

### 本地开发

```bash
# 1. 初始化项目
bash scripts/init.sh

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入实际配置

# 3. 启动全部服务
bash deploy/scripts/start.sh
```

### 服务端点

- **Java Service**: http://localhost:8080
- **Python AI Service**: http://localhost:8000
- **Actuator Health**: http://localhost:8080/actuator/health
- **API Docs (Python)**: http://localhost:8000/docs

## 项目结构

详见下方目录树。

## 开发规范

- **Java**: 遵循阿里巴巴 Java 开发手册，DDD 分层架构
- **Python**: 遵循 PEP8 规范，使用 Src Layout
- **命名**: 严格使用专业英文术语，禁止拼音及无意义缩写
- **测试**: 所有核心模块需配备对应的单元测试与集成测试
