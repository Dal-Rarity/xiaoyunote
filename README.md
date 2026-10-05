# 小语手记（xiaoyunote）

一个基于 Flask 的个人博客 / 手记社区：文章发布、富文本编辑、收藏夹、关注、消息通知、邮件验证码，并集成了基于 RAG 的 AI 对话助手（独立 FastAPI 服务）。

- 主站入口：`main.py`（Flask，端口 `5000`）
- AI 服务：`services/ai_service`（FastAPI，端口 `8100`）
- 本地开发执行 `python main.py` 会**自动拉起 AI 子进程**，一条命令启动整套服务。

## 功能一览

- 首页信息流、文章详情、富文本（UEditor Plus）写文 / 存草稿 / 随机头图
- 注册 / 登录（Redis 邮件验证码）、个人设置、头像上传
- 收藏、收藏夹、关注 / 粉丝、站内消息通知、意见反馈
- AI 助手：流式 SSE 对话，RAG 检索（Qdrant + bge-m3 + Rerank + 云端 LLM）

## 技术栈

| 层 | 技术 |
| --- | --- |
| 主站 | Python 3.11、Flask 2.3.3、SQLAlchemy 2.0、PyMySQL、redis-py、python-dotenv、Pillow |
| 前端 | Jinja2 模板、原生 JS + Axios、Bootstrap 5、UEditor Plus、iconfont |
| AI 服务 | FastAPI、Uvicorn、httpx、Qdrant、Redis、Ollama(bge-m3)、通义 DashScope、硅基流动 Rerank |
| 存储/中间件 | MySQL 8（utf8mb4）、Redis（db0=AI，db1=主站）、Qdrant（向量库） |
| 部署 | Docker、Docker Compose、Nginx（反代 + SSE） |

## 请求链路

```
浏览器
  └─ Nginx :80
       ├─ /                     → flask:5000   （页面 / 主站接口）
       ├─ /api/ai/chat/stream   → flask:5000   （AI 网关：校验登录 + 注入内部 Token，SSE 透传）
       └─ /health、/metrics      → ai:8100      （AI 服务健康检查，直连）

flask:5000 ── MySQL / Redis( db1 )
ai:8100   ── Qdrant / Redis(db0) / Ollama(bge-m3) / 云端 LLM、Rerank
```

> 注意：`/api/ai/chat/stream` **必须经 Flask 网关**，浏览器不能直连 AI 服务——直连请求缺少 `X-Internal-Token`，会被 AI 服务返回 401。

## 目录结构

```
xiaoyunote/
├── main.py                    # Flask 入口；本地自动拉起 AI 子进程，容器内只跑 Flask
├── requirements.txt           # 主站依赖
├── .env / .env.example        # 主站环境变量（.env 不入库）
├── Dockerfile / .dockerignore # 主站镜像
├── docker-compose.full.yml    # 虚拟机完整部署编排（nginx/flask/ai 三容器）
├── deploy/
│   └── nginx-full.conf        # Nginx 配置（含 SSE 反代）
├── app/                       # 应用工厂与配置
│   ├── app.py                 #   create_app()、SECRET_KEY 加载
│   ├── settings.py            #   FLASK_ENV
│   └── config/config.py       #   数据库 / 邮箱 / Redis 配置（读环境变量）
├── common/                    # 公共工具：数据库连接、Redis、邮件、响应封装
├── controller/                # 控制器层（Flask 蓝图）
├── model/                     # 模型层（SQLAlchemy 表模型与数据操作）
├── template/                  # 视图层（Jinja2 页面）
├── resource/                  # 前端静态资源（css/js/字体/图片/插件，随仓库提交）
│   └── upload/                #   用户上传内容（不入库，仅保留 .gitkeep）
├── log/                       # 运行日志（不入库，仅保留 .gitkeep）
├── tests/                     # 主站测试（AI 网关等）
└── services/
    └── ai_service/            # 独立 FastAPI AI 服务（拥有自己的 .venv / .env / Dockerfile）
        ├── ai_app/
        │   ├── main.py        #   FastAPI 入口
        │   ├── config.py      #   pydantic-settings 配置
        │   ├── routers/       #   chat / health / debug
        │   └── services/      #   检索、重排、LLM、向量库、缓存、对话管线
        ├── scripts/           # 语料同步 / 导出 / 评测脚本
        ├── tests/  docs/  deploy/
        └── requirements.txt
```

## 本地开发

### 1. 准备依赖服务

- MySQL 8：创建库 `xiaoyushouji`（字符集 `utf8mb4`）
- Redis
- Qdrant（AI 检索用）
- Ollama 并拉取 `bge-m3` 嵌入模型（AI 检索用）

### 2. 主站

```powershell
# 在项目根目录
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env   # 然后填入数据库 / 邮箱 / Redis 等真实配置
```

### 3. AI 服务（独立虚拟环境）

```powershell
cd services\ai_service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env   # 填入云端 LLM / Rerank / Dify 的 Key
```

> AI 首次使用前需同步语料到 Qdrant：
> `python scripts/sync_corpus.py`（从主站 MySQL 只读拉取文章，配置见 AI 服务 `.env` 的 `MYSQL_DSN`）。

### 4. 一键启动

回到项目根目录：

```powershell
python main.py
```

- 自动先启动 AI 子进程（`127.0.0.1:8100`），等 `/health` 就绪后再启动 Flask；
- 访问 <http://127.0.0.1:5000>；
- 如不想拉起 AI 子进程：`$env:START_AI_CHILD=0`。

## 环境变量

### 根目录 `.env`（Flask 主站）

| 变量 | 说明 |
| --- | --- |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` / `DB_CHARSET` | MySQL 连接（本地开发端口按实际填写；容器由 compose 覆盖为宿主 3306） |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | 发件邮箱与 **SMTP 授权码**（非登录密码） |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD` / `REDIS_DB` | Redis，主站用 db1；无密码时 `REDIS_PASSWORD=` 留空 |
| `FLASK_ENV` | `test` / `production` |
| `SECRET_KEY` | Flask 会话密钥；未设置时回退读取 `.secret_key` 文件，再没有则自动生成 |
| `AI_SERVICE_URL` | Flask 调用 AI 服务的地址（本地 `http://127.0.0.1:8100`，容器 `http://ai:8100`） |
| `AI_INTERNAL_TOKEN` | 调用 AI 服务的内部 Token，**必须与 AI 服务的 `INTERNAL_TOKEN` 一致** |
| `START_AI_CHILD` | 可选。`main.py` 是否自动拉起 AI 子进程；本地默认 `1`，容器内默认 `0` |
| `FLASK_RUN_HOST` / `FLASK_RUN_PORT` | 可选。Flask 监听地址/端口，默认 `127.0.0.1:5000`；镜像内由 Dockerfile 注入 `0.0.0.0` |
| `RUNNING_IN_DOCKER` | 容器标识，Dockerfile 自动置为 `1`（也可通过 `/.dockerenv` 探测），无需在 `.env` 中配置 |

### `services/ai_service/.env`（AI 服务）

| 变量 | 说明 |
| --- | --- |
| `INTERNAL_TOKEN` | 内部鉴权 Token，与主站 `AI_INTERNAL_TOKEN` 保持一致 |
| `LLM_API_KEY` | 通义 DashScope Key |
| `RERANK_API_KEY` | 硅基流动 Rerank Key |
| `DIFY_API_KEY` | **预留项，当前运行时不读取**（配置类忽略多余变量，Dify 导入脚本用脚本内硬编码配置），可留空或删除 |
| `MYSQL_DSN` | 主站 MySQL 只读 DSN，供 `scripts/sync_corpus.py` 同步语料 |
| `EMBED_BASE_URL` / `QDRANT_URL` / `REDIS_URL` | Ollama / Qdrant / Redis 地址，默认值见 `ai_app/config.py` |

> 容器部署时，`QDRANT_URL`、`REDIS_URL`、`EMBED_BASE_URL`、`INTERNAL_TOKEN`、`MYSQL_DSN` 由 `docker-compose.full.yml` 的 `environment` 覆盖，以 compose 为准。

## Docker 部署（虚拟机）

部署目标：Ubuntu 虚拟机（示例 `192.168.56.200`），编排文件 `docker-compose.full.yml` 只启动 **nginx / flask / ai** 三个容器，MySQL / Redis / Qdrant **复用宿主已有服务**（经 `host.docker.internal` 访问）。

前置条件：

1. 宿主 MySQL 监听 `0.0.0.0:3306`，业务账号已授权远程登录（如 `xiaoyu@'%'`），库与表已初始化；
2. 宿主 Redis 监听 `0.0.0.0:6379`；Qdrant 监听 `0.0.0.0:6333`；
3. 嵌入模型 Ollama 监听 `0.0.0.0:11434`（compose 中按实际主机 IP 配置 `EMBED_BASE_URL`）；
4. 项目根目录与 `services/ai_service/` 下各放一份真实 `.env`。

```bash
cd ~/xiaoyunote
docker compose -f docker-compose.full.yml up -d --build
# 访问 http://192.168.56.200/
```

容器内 `main.py` 检测到 `RUNNING_IN_DOCKER=1` 后不再拉起 AI 子进程（AI 是独立容器），Flask 监听 `0.0.0.0:5000`。用户上传目录 `resource/upload/` 与 `log/` 通过卷挂载持久化到宿主项目目录。

### 常用运维命令

```bash
docker compose -f docker-compose.full.yml ps          # 查看三容器状态
docker compose -f docker-compose.full.yml logs -f flask
docker compose -f docker-compose.full.yml restart ai
docker compose -f docker-compose.full.yml up -d --build flask   # 仅重建主站
docker compose -f docker-compose.full.yml down        # 停止并移除容器（不删数据）
```

## Git 与安全约定

- `.env`、`services/ai_service/.env`、`.secret_key` 均被 `.gitignore` 忽略，**严禁提交真实密钥**；新环境从对应的 `.env.example` 复制。
- `resource/` 下的样式、脚本、字体、默认图片、第三方插件**随仓库提交**；只有用户运行时产物不入库：
  - `resource/upload/*`（保留 `.gitkeep`）
  - 用户头像 `resource/images/headers/user_*.jpg`（默认头图 `1.jpg`~`20.jpg` 入库）
  - `log/*`（保留 `.gitkeep`）
- 提交前建议检查暂存内容：`git diff --cached --name-only`，确认没有密钥与用户数据。

## 默认账号

本地 / 初始化数据中的测试账号：用户名与密码均为 `123456`（仅供开发测试，正式环境请修改）。
