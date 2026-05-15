import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.chat import router as chat_router
from routers.knowledge import router as knowledge_router

app = FastAPI(
    title="AgentStudio - Python Agent Service",
    description="LangChain + LangGraph powered AI agent backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(knowledge_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent"}


@app.get("/")
async def root():
    return {
        "service": "AgentStudio Agent Service",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
