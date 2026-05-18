# AgentStudio — 企业级 AI 智能体平台

> 一站式 RAG / GraphRAG / Agent / 评测 / 语音的生产级参考实现。

![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![Go](https://img.shields.io/badge/Go-1.22+-00ADD8?logo=go)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-orange)
![LangSmith](https://img.shields.io/badge/LangSmith-Tracing-eab308)
![Chroma](https://img.shields.io/badge/Chroma-Vector-7c3aed)
![Milvus](https://img.shields.io/badge/Milvus-Optional-1d4ed8)
![Neo4j](https://img.shields.io/badge/Neo4j-GraphRAG-008cc1)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

## ✨ 核心特性

| 模块 | 能力 |
|------|------|
| **知识库** | PDF / DOCX / MD / TXT / HTML 解析 · 智能切片 · 多文档管理 · 检索调试面板 |
| **多路召回** | 向量(Chroma/Milvus) + BM25(内存/Elasticsearch) + GraphRAG(Neo4j) · RRF 融合 |
| **重排** | 默认 RRF · 可选 BAAI/bge-reranker-base CrossEncoder |
| **GraphRAG** | LLM 实体抽取 → Neo4j 图谱 → 实体邻居反查相关 chunks |
| **会话** | LangGraph 编排 · SSE 流式输出 · 引用 citations · 历史持久化 |
| **评测** | 多指标(语义相似 / Faithfulness / Answer Relevance) · 批量运行 · LangSmith 追踪 |
| **语音** | OpenAI Whisper STT · OpenAI TTS · Web Speech 兜底 |
| **可观测** | LangSmith 一键启用 · 结构化日志 · 链路 latency |

## 🏗 架构总览

```
┌───────────────┐    JWT     ┌────────────┐   HTTP/SSE   ┌──────────────────┐
│ Next.js 16    │◄────────►  │ Go Gateway │  ◄────────►  │ Python Agent     │
│ Tailwind v4   │            │ Gin + JWT  │              │ FastAPI+LangGraph│
└───────────────┘            └────────────┘              └────────┬─────────┘
                                                                  │
       ┌────────────────────────┬─────────────────────────────────┼───────────┬────────────┐
       ▼                        ▼                                 ▼           ▼            ▼
┌─────────────┐         ┌──────────────┐                  ┌──────────┐  ┌────────┐  ┌──────────┐
│  Postgres   │         │ Chroma/Milvus│                  │  BM25 /  │  │ Neo4j  │  │ OpenAI   │
│ (会话/评测) │         │  (向量召回)  │                  │  ES (倒排)│  │ (图谱) │  │ LLM/语音 │
└─────────────┘         └──────────────┘                  └──────────┘  └────────┘  └──────────┘
```

## 🧱 项目结构

```
ai-demo/
├── frontend/                  Next.js 16 + Tailwind v4 + Zustand
│   └── src/
│       ├── app/
│       │   ├── chat/         会话(SSE 流式 / 引用 / 语音输入 / TTS)
│       │   ├── knowledge/    知识库(上传 / 文档 / 检索调试)
│       │   └── eval/         评测(用例 CRUD / 批量运行 / 多指标)
│       ├── components/
│       │   ├── layout/       Sidebar / Header / WorkspaceSelector
│       │   └── ui/           Modal / Markdown / Toast
│       └── lib/              api / speech / markdown
├── gateway/                   Go + Gin + JWT(支持 SSE 转发)
└── agent/                     Python 3.10+ + FastAPI + LangGraph
    ├── agents/               LangGraph Chat Agent
    ├── rag/                  多路召回流水线
    │   ├── embeddings.py    OpenAI / HF 嵌入工厂
    │   ├── vector_store.py  Chroma / Milvus 适配
    │   ├── bm25.py          内存 / Elasticsearch
    │   ├── reranker.py      RRF / CrossEncoder
    │   ├── splitter.py      文档解析 + 切片
    │   └── pipeline.py      ingest / retrieve 编排
    ├── graph/                GraphRAG (Neo4j)
    ├── evaluation/           评测引擎 + 指标
    ├── voice/                STT / TTS
    ├── routers/              FastAPI 路由
    ├── schemas/              Pydantic Schemas
    └── db/                   SQLAlchemy 模型
```

## 🚀 快速启动

### 方式一:Docker Compose(推荐)

```bash
# 1. 复制配置
cp agent/.env.example agent/.env
# 编辑 agent/.env,填入 OPENAI_API_KEY

# 2. 仅启动核心(Chroma + 内存 BM25)
docker compose up -d

# 3. 启用 Milvus / Elasticsearch / Neo4j(任选)
docker compose --profile milvus up -d
docker compose --profile es up -d
docker compose --profile neo4j up -d
docker compose --profile full up -d   # 全部启用

# 配合环境变量
VECTOR_STORE=milvus MILVUS_URI=http://milvus:19530 docker compose --profile milvus up -d
BM25_BACKEND=elasticsearch ES_URL=http://elasticsearch:9200 docker compose --profile es up -d
ENABLE_GRAPHRAG=true NEO4J_URI=bolt://neo4j:7687 docker compose --profile neo4j up -d
```

### 方式二:本地开发

```bash
./scripts/setup.sh    # 一次性初始化
echo "OPENAI_API_KEY=sk-your-real-key" > agent/.env
./scripts/start.sh    # 启动 前端 + 网关 + Agent
```

或分别启动:

```bash
cd frontend && npm run dev                                  # :3000
cd agent    && source .venv/bin/activate && python main.py  # :8000
cd gateway  && go run .                                     # :8080
```

## 📡 访问地址

| 服务 | URL |
|------|-----|
| 前端 UI | http://localhost:3000 |
| Go 网关 | http://localhost:8080 |
| Agent API | http://localhost:8000 |
| Agent OpenAPI | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 (`--profile neo4j`) |

## ⚙️ 环境变量

agent/.env 完整列表见 [`agent/.env.example`](./agent/.env.example)。常用项:

| 变量 | 默认 | 说明 |
|------|------|------|
| `OPENAI_API_KEY` | — | 必填,无效时所有 LLM/嵌入降级为 demo 模式 |
| `OPENAI_MODEL` | `gpt-4o-mini` | 主对话模型 |
| `EMBEDDING_PROVIDER` | `auto` | `auto/openai/huggingface` |
| `VECTOR_STORE` | `chroma` | `chroma/milvus` |
| `MILVUS_URI` | — | 启用 Milvus 时填 |
| `BM25_BACKEND` | `memory` | `memory/elasticsearch` |
| `ES_URL` | — | 启用 ES 时填 |
| `ENABLE_GRAPHRAG` | `false` | `true` 启用 GraphRAG |
| `NEO4J_URI` | — | 启用 GraphRAG 时填 |
| `RERANKER` | `rrf` | `rrf/cross_encoder` |
| `RAG_TOP_K` | `5` | 注入 LLM 的上下文条数 |
| `RAG_RECALL_K` | `12` | 多路召回每路的候选数 |
| `LANGCHAIN_TRACING_V2` | — | `true` 开启 LangSmith |
| `LANGCHAIN_API_KEY` | — | LangSmith Key |

## 🔌 API 速览

详细 OpenAPI 见 http://localhost:8000/docs。Gateway 前置 JWT 鉴权,统一转发至 Agent。

```http
POST /api/auth/login                 # 登录 → JWT

# 知识库
GET    /api/knowledge/bases
POST   /api/knowledge/bases
PATCH  /api/knowledge/bases/{id}
DELETE /api/knowledge/bases/{id}
POST   /api/knowledge/bases/{id}/upload         # multipart 上传
GET    /api/knowledge/bases/{id}/documents
DELETE /api/knowledge/bases/{id}/documents/{docId}
POST   /api/knowledge/bases/{id}/retrieve       # 检索调试

# 会话
POST   /api/chat/completions                    # 同步
POST   /api/chat/stream                         # SSE 流式
GET    /api/chat/conversations
GET    /api/chat/conversations/{id}/messages
DELETE /api/chat/conversations/{id}

# 评测
GET    /api/eval/cases | POST | PATCH | DELETE
POST   /api/eval/cases/{id}/run
POST   /api/eval/runs/batch
GET    /api/eval/summary

# 语音
POST   /api/voice/transcribe                    # multipart audio → text
POST   /api/voice/synthesize                    # text → mp3
```

### SSE 事件

`POST /api/chat/stream` 返回的事件流:

```
data: {"event":"conversation","conversation_id":"..."}
data: {"event":"retrieved","chunks":[{...}]}    # 多路召回结果
data: {"event":"token","text":"R"}
data: {"event":"token","text":"AG "}
data: {"event":"done","content":"...","chunks":[...]}
```

## 🧠 RAG 流水线

```
ingest:  上传 → 解析(pdf/docx/md/txt/html)
              → 递归切片
              → Chunks 落 SQL
              → 向量库 (Chroma / Milvus)
              → BM25 (内存 / Elasticsearch)
              → [可选] LLM 抽实体 → Neo4j

retrieve: query
   ├─ 向量召回 (top recall_k)
   ├─ BM25 召回 (jieba 中文分词)
   ├─ [可选] GraphRAG 实体邻居召回
   ├─ RRF 融合
   ├─ [可选] CrossEncoder 重排
   └─ 取 top_k → 注入 system prompt → LLM
```

## 📊 评测指标

| 指标 | 计算方式 | 权重 |
|------|---------|------|
| Semantic Similarity | 期望/实际 答案 embedding cosine | 0.40 |
| Faithfulness | LLM-as-judge,基于检索上下文的事实性 | 0.35 |
| Answer Relevance | LLM-as-judge,答案与问题的相关性 | 0.25 |

综合分 ≥ 0.7 视为通过。配置 `LANGCHAIN_TRACING_V2=true` 后所有评测调用自动上报 LangSmith。

## 🛠 技术选型说明

- **不强制依赖重型服务**:Chroma + 内存 BM25 即可开箱跑通完整链路。
- **可插拔架构**:`vector_store.py` / `bm25.py` / `graphrag.py` 都是接口 + 适配器,启用 Milvus / ES / Neo4j 只需配置环境变量。
- **降级友好**:OPENAI_API_KEY 缺失时,嵌入自动降级 FakeEmbeddings,LLM 返回 demo 提示,链路依旧可演示。
- **生产可用要点**:统一鉴权 / 工作区隔离 / 异步 SQLAlchemy / SSE 流式 / 错误透传 / 结构化日志 / Compose Profiles 部署。

## 🔒 安全 / 暴露面收敛(合规整改)

为满足"AI 服务暴露面收敛"合规要求,本项目内置以下两层防护,默认即合规:

### 1) 监听地址原则:仅 127.0.0.1,严禁 0.0.0.0

| 服务 | 本地直跑 | Docker 部署 |
|------|----------|-------------|
| Frontend (Next.js) | `next dev -H 127.0.0.1` | 容器内 `0.0.0.0`,宿主机 `127.0.0.1:3000` 映射 |
| Gateway (Go/Gin) | `HOST=127.0.0.1 PORT=8080` | 容器内 `0.0.0.0`,宿主机 `127.0.0.1:8080` 映射 |
| Agent (FastAPI) | `HOST=127.0.0.1 PORT=8000` | 容器内 `0.0.0.0`,**默认不向宿主机映射**(仅供 gateway 通过 docker network 内网调用) |
| Postgres / Redis / Milvus / ES / Neo4j | — | **默认不向宿主机映射**,仅 docker network 内通信 |

> 容器内必须监听 `0.0.0.0` 才能跨容器被访问,**收敛由宿主机端口映射 `127.0.0.1:<port>:<port>` 完成**,这是 Docker 场景下最小暴露面的标准做法。

### 2) 跨主机调用:IP + 端口双重白名单

如果确有其他业务系统需跨本机调用 AI 服务,请按"应用层白名单 + 网络层防火墙"两层配置:

#### 应用层(已内置中间件)

`agent/.env`(或 `gateway` 同名环境变量):

```bash
# 跨主机授信网段(逗号分隔,支持单 IP / CIDR)
IP_ALLOWLIST=10.0.0.0/8,192.168.10.5

# CORS 显式来源(严禁 "*")
CORS_ALLOWED_ORIGINS=https://internal.example.com,http://127.0.0.1:3000

# 仅在前置可信反代/网关时开启,否则会被 X-Forwarded-For 伪造头绕过
TRUST_PROXY=false
```

中间件位置:

- Agent: `agent/middleware/ip_allowlist.py` → `IPAllowlistMiddleware`
- Gateway: `gateway/middleware/ipallowlist.go` → `middleware.IPAllowlist`

未命中白名单的请求统一返回 `403 FORBIDDEN`,并打印 `IPAllowlist: 拒绝来自 <ip>` 审计日志。

#### 网络层(运维侧补强)

Linux 主机请配合防火墙做"端口 + 源 IP"双重收敛(以 nftables / iptables / firewalld 三选一):

```bash
# 1. iptables: 仅放行 10.0.0.0/8 访问 8080(网关), 默认 DROP
iptables -A INPUT -p tcp --dport 8080 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -s 127.0.0.1   -j ACCEPT
iptables -A INPUT -p tcp --dport 8080                -j DROP
# 数据库类端口 一律仅本地回环
iptables -A INPUT -p tcp -m multiport --dports 5432,6379,9200,7474,7687,19530 ! -s 127.0.0.1 -j DROP

# 2. ufw 等价配置 (Ubuntu)
ufw default deny incoming
ufw allow from 10.0.0.0/8 to any port 8080 proto tcp
ufw allow from 127.0.0.1   to any port 8080 proto tcp
```

云上部署请同步在**安全组 / VPC ACL**中按此原则限制源 IP + 端口,与主机防火墙互为冗余。

### 3) 自检清单

- [ ] `ss -tlnp | grep -E ':(3000|8080|8000|5432|6379|9200|7474|7687|19530)'` 输出的 Local Address 必须全部为 `127.0.0.1` 或容器内网,**严禁 `0.0.0.0`**。
- [ ] `agent/.env` 与 gateway 环境变量中 `CORS_ALLOWED_ORIGINS` 不含 `*`。
- [ ] 跨主机调用方 IP 已加入 `IP_ALLOWLIST`,未授信主机访问得到 403。
- [ ] 主机防火墙 / 云安全组对 8080(网关)、3000(前端)外的端口默认 DROP。

## 📝 License

MIT
