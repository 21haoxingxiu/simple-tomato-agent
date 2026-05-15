#!/bin/bash
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "=== AgentStudio 初始化 ==="

# Check Go
if ! command -v go &>/dev/null; then
  echo "⚠️  Go 未安装，请先安装 Go 1.22+"
  echo "   brew install go"
  echo "   或访问 https://go.dev/dl/"
  HAS_GO=false
else
  HAS_GO=true
  echo "✅ Go: $(go version)"
fi

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "⚠️  Python3 未安装"
  HAS_PY=false
else
  HAS_PY=true
  echo "✅ Python: $(python3 --version)"
fi

# Check Node
if ! command -v node &>/dev/null; then
  echo "⚠️  Node.js 未安装"
  HAS_NODE=false
else
  HAS_NODE=true
  echo "✅ Node: $(node --version)"
fi

echo ""
echo "=== 安装依赖 ==="

# Frontend
if [ "$HAS_NODE" = true ]; then
  echo "📦 安装前端依赖..."
  cd "$ROOT/frontend" && npm install
fi

# Go gateway
if [ "$HAS_GO" = true ]; then
  echo "📦 安装 Go 依赖..."
  cd "$ROOT/gateway" && go mod tidy
fi

# Python agent
if [ "$HAS_PY" = true ]; then
  echo "📦 安装 Python 依赖..."
  cd "$ROOT/agent"
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
  fi
  source .venv/bin/activate
  pip install -r requirements.txt
  if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  请编辑 agent/.env 填入 OPENAI_API_KEY"
  fi
fi

echo ""
echo "✅ 初始化完成！"
echo ""
echo "启动方式："
echo "  ./scripts/start.sh        # 启动所有服务"
echo "  docker compose up -d      # Docker 方式启动"
