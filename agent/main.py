"""AgentStudio - Python Agent Service.

提供:
- 知识库管理 (多路召回 + 重排 + GraphRAG 可选)
- 会话(同步 + SSE 流式 + 引用)
- 评测(单条/批量 + 多指标 + LangSmith 上报)
- 语音(STT/TTS)
"""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

load_dotenv()

# LangSmith 自动启用(用户在 .env 配置 LANGCHAIN_TRACING_V2=true)
if os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true":
    os.environ.setdefault("LANGCHAIN_PROJECT", "agentstudio")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from db.database import init_db  # noqa: E402
from middleware.ip_allowlist import IPAllowlistMiddleware, from_env as _ip_from_env  # noqa: E402
from routers.auth import router as auth_router  # noqa: E402
from routers.chat import router as chat_router  # noqa: E402
from routers.evaluation import router as eval_router  # noqa: E402
from routers.knowledge import router as knowledge_router  # noqa: E402
from routers.voice import router as voice_router  # noqa: E402


def _split_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AgentStudio - Agent Service",
    description="LangChain + LangGraph + 多路召回 + GraphRAG + 评测 + 语音",
    version="0.2.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# 安全中间件
# 1) IP 白名单: 默认仅放行本地回环 (127.0.0.0/8 + ::1), 跨主机调用需在 IP_ALLOWLIST
#    显式配置授信网段, 与端口 + 防火墙形成 "IP + 端口" 双重白名单.
# 2) CORS: 通过 CORS_ALLOWED_ORIGINS 显式配置可信来源, 严禁使用通配符 "*".
# ---------------------------------------------------------------------------
_allow_nets, _trust_proxy = _ip_from_env()
app.add_middleware(
    IPAllowlistMiddleware,
    allowlist=_allow_nets,
    trust_proxy=_trust_proxy,
)

_cors_origins = _split_csv(os.getenv("CORS_ALLOWED_ORIGINS")) or ["http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Workspace-ID", "X-User-ID", "Accept"],
    expose_headers=["Content-Type", "Content-Disposition"],
    allow_credentials=True,
    max_age=86400,
)


app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(knowledge_router)
app.include_router(eval_router)
app.include_router(voice_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent", "version": app.version}


@app.get("/")
async def root():
    return {
        "service": "AgentStudio Agent Service",
        "version": app.version,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    # 默认仅监听本地回环, 严禁 0.0.0.0;
    # 容器场景由 Dockerfile/compose 通过 HOST 环境变量显式声明绑定行为.
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENV", "development").lower() != "production"
    uvicorn.run("main:app", host=host, port=port, reload=reload)
