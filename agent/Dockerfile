FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 编译 jieba/lxml/壹些 wheel 需要的最小 toolchain
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/data

# 容器内监听地址通过 HOST 环境变量声明:
#   - 推荐: HOST=127.0.0.1 (容器与宿主机/网关同 network namespace, 例如 host network 模式);
#   - 仅当容器需供 docker network 内的其他容器调用时才使用 0.0.0.0,
#     此时务必通过 docker-compose 中的 "127.0.0.1:<port>:<port>" 限定宿主端口暴露面.
ENV HOST=127.0.0.1 \
    PORT=8000

EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host \"${HOST}\" --port \"${PORT}\""]
