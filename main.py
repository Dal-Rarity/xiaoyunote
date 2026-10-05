# 不增加AI应用助手时
# from app.app import create_app
# import logging
#
# app = create_app()
#
#
# if __name__ == '__main__':
#     logging.info("我是info级别的日志")
#     logging.debug("我是debug级别的日志")
#     app.run()
#     # ai_app.run(debug=True)
#     # print(ai_app.url_map)

from app.app import create_app
import logging

import atexit
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request

# ==================== 一键启动 FastAPI ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AI_DIR = os.path.join(BASE_DIR, "services", "ai_service")

# ai_service 自己的虚拟环境（不要用 flask_project 的 Python）
if sys.platform == "win32":
    AI_PYTHON = os.path.join(AI_DIR, ".venv", "Scripts", "python.exe")
else:
    AI_PYTHON = os.path.join(AI_DIR, ".venv", "bin", "python")

AI_HOST = "127.0.0.1"
AI_PORT = 8100
AI_HEALTH = f"http://{AI_HOST}:{AI_PORT}/health"

_ai_proc: subprocess.Popen | None = None


def _port_free(host: str, port: int) -> bool:
    """端口是否空闲"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) != 0


def _ai_running() -> bool:
    """FastAPI 是否已在运行"""
    try:
        with urllib.request.urlopen(AI_HEALTH, timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def start_ai_service() -> subprocess.Popen | None:
    """启动 FastAPI 子进程"""
    if _ai_running():
        print("[跳过] FastAPI 已在运行")
        return None

    if not os.path.exists(AI_PYTHON):
        print(f"[ERROR] 找不到 AI 服务虚拟环境：{AI_PYTHON}")
        print("请先执行：cd services/ai_service && python -m venv .venv && pip install -r requirements.txt")
        sys.exit(1)

    if not _port_free(AI_HOST, AI_PORT):
        print(f"[ERROR] 端口 {AI_PORT} 被占用，请先关闭占用进程")
        sys.exit(1)

    cmd = [
        AI_PYTHON, "-m", "uvicorn",
        "ai_app.main:app",
        "--host", AI_HOST,
        "--port", str(AI_PORT),
    ]
    print(f"[启动] FastAPI: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=AI_DIR, stdout=sys.stdout, stderr=sys.stderr)


def wait_for_ai_ready(timeout: int = 30) -> bool:
    """等 FastAPI /health 返回 200"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if _ai_running():
            print(f"[就绪] FastAPI 已启动（{int(time.time() - t0)}s）")
            return True
        time.sleep(0.5)
    print(f"[WARN] FastAPI 未在 {timeout}s 内就绪，继续启动 Flask")
    return False


def stop_ai_service():
    """关闭 FastAPI 子进程"""
    global _ai_proc
    if _ai_proc and _ai_proc.poll() is None:
        print("\n[关闭] FastAPI 服务")
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(_ai_proc.pid)],
                    capture_output=True,
                )
            else:
                _ai_proc.terminate()
                _ai_proc.wait(timeout=5)
        except Exception:
            try:
                _ai_proc.kill()
            except Exception:
                pass


# ==================== 应用入口 ====================
app = create_app()


def _in_container() -> bool:
    """是否运行在容器中：Dockerfile 会显式设置 RUNNING_IN_DOCKER=1"""
    return os.getenv("RUNNING_IN_DOCKER", "") == "1" or os.path.exists("/.dockerenv")


# 本地开发默认一键拉起 FastAPI 子进程；容器内 AI 是独立容器，默认不拉起
# 两种环境都可用环境变量 START_AI_CHILD=1/0 显式覆盖
_default_start_ai = "0" if _in_container() else "1"
START_AI_CHILD = os.getenv("START_AI_CHILD", _default_start_ai) == "1"

# 容器内必须监听 0.0.0.0（Dockerfile 注入 FLASK_RUN_HOST）；本地默认仅本机
FLASK_HOST = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_RUN_PORT", "5000"))


if __name__ == '__main__':
    # 1. 本地开发模式：拉起 FastAPI 子进程（容器内跳过）
    if START_AI_CHILD:
        # Ctrl+C / 异常退出时，一起关闭 FastAPI
        atexit.register(stop_ai_service)
        signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

        _ai_proc = start_ai_service()
        wait_for_ai_ready()

    # 2. 启动 Flask 主站
    logging.info("我是info级别的日志")
    logging.debug("我是debug级别的日志")
    print(f"[启动] Flask 主站 http://{FLASK_HOST}:{FLASK_PORT}（AI 子进程: {'开启' if START_AI_CHILD else '关闭'}）")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)

    # ai_app.run(debug=True)
    # print(ai_app.url_map)
