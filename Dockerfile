# Flask 主站镜像（小语手记）
FROM python:3.11-slim

WORKDIR /app

# 依赖均有预编译 wheel（Pillow / PyMySQL），无需 gcc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝项目代码（resource 静态资源需要进镜像；.env/.secret_key 由 .dockerignore 排除）
COPY . .

# 日志与上传目录（上传目录运行时以 volume 覆盖持久化）
RUN mkdir -p log resource/upload resource/images/headers

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    RUNNING_IN_DOCKER=1 \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000

EXPOSE 5000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/', timeout=5).status == 200 else 1)" || exit 1

CMD ["python", "main.py"]
