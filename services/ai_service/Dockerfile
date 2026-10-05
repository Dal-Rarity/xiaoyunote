# FastAPI AI 服务镜像（小语手记 · ai_service）
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# .env 不打进镜像（运行时由 compose env_file / environment 注入）
COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8100

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8100/health', timeout=5).status == 200 else 1)" || exit 1

CMD ["uvicorn", "ai_app.main:app", "--host", "0.0.0.0", "--port", "8100"]
