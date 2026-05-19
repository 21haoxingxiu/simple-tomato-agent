#!/bin/bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== 启动 AgentStudio ==="
echo "Frontend  → http://localhost:3000"
echo "Gateway   → http://localhost:8080"
echo "Agent API → http://localhost:8000"
echo "Agent Docs→ http://localhost:8000/docs"
echo ""
echo "Ctrl+C 停止所有服务"
echo ""

# Trap to kill all children on exit
trap 'kill 0' SIGINT SIGTERM

# Start Python agent
echo "🐍 Starting Python Agent..."
cd "$ROOT/agent"
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi
python3 main.py &
PY_PID=$!

# Start Go gateway
if command -v go &>/dev/null; then
  echo "🔵 Starting Go Gateway..."
  cd "$ROOT/gateway"
  CORS_ALLOWED_ORIGINS="http://127.0.0.1:3000,http://localhost:3000" go run . &
  GO_PID=$!
fi

# Start Next.js frontend
echo "⚡ Starting Next.js Frontend..."
cd "$ROOT/frontend"
npm run dev &
NEXT_PID=$!

wait
