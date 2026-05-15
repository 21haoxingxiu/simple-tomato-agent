# AgentStudio — AI 智能体平台

> 一个从零搭建的全栈 Agent 系统，用于学习 Go 和 Python 的工程实践。

![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![Go](https://img.shields.io/badge/Go-1.22+-00ADD8?logo=go)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-orange)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Next.js 16 + TypeScript + Tailwind | 页面 UI、路由、状态管理 |
| 网关 | Go + Gin + JWT | API 网关、鉴权、反向代理 |
| Agent | Python + FastAPI + LangGraph | AI 推理、RAG、工作流编排 |
| 数据库 | PostgreSQL + Redis | 持久化 + 缓存 |

## 项目结构

```
ai-demo/
├── frontend/          # Next.js 前端
│   └── src/
│       ├── app/
│       │   ├── chat/          # 会话聊天页
│       │   ├── knowledge/     # 知识库页
│       │   └── eval/          # 评测页
│       ├── components/layout/ # Sidebar, Header, WorkspaceSelector
│       ├── store/             # Zustand 状态管理
│       └── types/             # TypeScript 类型定义
├── gateway/           # Go API 网关
│   ├── main.go
│   ├── config/        # 配置加载
│   ├── middleware/    # JWT 鉴权中间件
│   └── handlers/      # 路由处理器 + 反向代理
├── agent/             # Python Agent 服务
│   ├── main.py        # FastAPI 入口
│   ├── agents/        # LangGraph 智能体图
│   ├── routers/       # API 路由
│   └── schemas/       # Pydantic 数据模型
├── scripts/           # 启动 & 初始化脚本
└── docker-compose.yml # 完整服务编排
```

## 快速启动

### 方式一：Docker Compose（推荐）

```bash
# 配置 OpenAI Key
cp agent/.env.example agent/.env
# 编辑 agent/.env，填入 OPENAI_API_KEY

# 一键启动所有服务
docker compose up -d
```

### 方式二：本地开发

**前提依赖**

- Node.js 20+
- Python 3.11+
- Go 1.22+

**1. 初始化**

```bash
./scripts/setup.sh
```

**2. 配置环境变量**

```bash
echo "OPENAI_API_KEY=sk-your-key" > agent/.env
```

**3. 启动所有服务**

```bash
./scripts/start.sh
```

或分别启动：

```bash
# 前端（3000 端口）
cd frontend && npm run dev

# Python Agent（8000 端口）
cd agent && source .venv/bin/activate && python3 main.py

# Go 网关（8080 端口）
cd gateway && go run .
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端 UI | http://localhost:3000 |
| Go 网关 | http://localhost:8080 |
| Agent API | http://localhost:8000 |
| Agent Swagger | http://localhost:8000/docs |

## 核心功能

- **工作区切换**：顶部可切换不同工作区，实现环境隔离
- **知识库管理**：上传文档，查看索引状态，支持 RAG 检索
- **会话聊天**：与 AI 智能体对话（接入 LangGraph 工作流）
- **评测中心**：测试用例管理，评估 AI 回答质量

## LangGraph Agent 架构

```
START → router → [retriever(RAG) | direct_llm] → generator → END
```

- `router`：判断是否需要检索知识库
- `retriever`：向量检索（待接入向量数据库）
- `generator`：调用 LLM 生成最终回答

## 安装 Go（如未安装）

```bash
brew install go
# 或从 https://go.dev/dl/ 下载安装包
```

安装后运行：

```bash
cd gateway && go mod tidy && go run .
```
