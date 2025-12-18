# =========================
# Build stage
# =========================
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# 系统依赖（如 cryptography）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 hatch
RUN pip install --no-cache-dir hatch

# 复制项目
COPY pyproject.toml README.md ./
COPY src ./src

# 构建 wheel
RUN hatch build -t wheel


# =========================
# Runtime stage
# =========================
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 运行期系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi8 \
    && rm -rf /var/lib/apt/lists/*

# 复制 wheel
COPY --from=builder /build/dist/*.whl /app/
COPY prompt/ cd /app/prompt/
# 安装运行期依赖
RUN pip install --no-cache-dir *.whl \
    && rm -f *.whl

# 非 root 运行
RUN useradd -m appuser
USER appuser

EXPOSE 5001

# 默认启动 server
CMD ["gunicorn", "liquibase_agent.server.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "4", \
     "-b", "0.0.0.0:5001"]