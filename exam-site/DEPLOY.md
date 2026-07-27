# 宝塔 + Docker 部署完整指南

## 前置条件

- 已安装宝塔面板（Linux）
- 服务器内存 ≥ 2G，磁盘 ≥ 10G
- 开放端口：80（前端）、8000（后端，可选，仅调试用）

---

## 第一步：安装 Docker

宝塔面板 → 软件商店 → 搜索 `Docker` → 安装「Docker 管理器」

安装完成后终端验证：

```bash
docker --version
docker compose version
```

---

## 第二步：上传项目文件

### 方式一：宝塔文件管理上传

1. 宝塔面板 → 文件 → 进入 `/www/wwwroot/`
2. 新建目录 `exam-site`
3. 将以下文件/文件夹上传到 `/www/wwwroot/exam-site/`：

```
exam-site/
├── backend/              # 整个后端目录
├── frontend/             # 整个前端目录（含 Dockerfile、nginx.conf 等）
├── doc/                  # 文档目录（RAG 索引用）
├── docker-compose.yml    # Docker Compose 编排文件
├── .env                  # 环境变量配置（含 API Key）
├── .env.example          # 环境变量模板
└── .dockerignore         # Docker 忽略文件
```

### 方式二：Git 拉取

```bash
cd /www/wwwroot
git clone <你的仓库地址> exam-site
```

---

## 第三步：配置环境变量

编辑 `/www/wwwroot/exam-site/.env`：

```env
OPENAI_API_KEY=你的StepFun_API_Key
OPENAI_MODEL=step-3.7-flash
OPENAI_BASE_URL=https://api.stepfun.com/step_plan/v1
OPENAI_TIMEOUT_SECONDS=30
```

---

## 第四步：构建并启动

### 终端方式（推荐）

```bash
cd /www/wwwroot/exam-site

# 构建镜像并启动（后台运行）
docker compose up -d --build

# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 宝塔 Docker 管理器方式

1. 宝塔面板 → Docker → 容器
2. 点击「添加」→「Compose 模板」
3. 模板名称：`exam-site`
4. 将 `docker-compose.yml` 内容粘贴进去
5. 点击「启动」

---

## 第五步：检查启动状态

```bash
# 检查容器是否运行
docker compose ps

# 预期输出：
# NAME               STATUS          PORTS
# exam-backend       Up (healthy)    0.0.0.0:8000->8000/tcp
# exam-frontend      Up (healthy)    0.0.0.0:80->80/tcp

# 检查后端日志（确认 RAG 索引构建成功）
docker logs exam-backend

# 应该看到类似输出：
# [Startup] Building RAG document index...
# [DocParser] Parsing PDF: ...
# [DocParser] Parsing .doc: ...
# [Startup] RAG index ready: 329 doc chunks + 500 question chunks, 27770 unique terms
```

---

## 第六步：访问验证

| 服务 | 地址 |
|------|------|
| 前端页面 | http://你的服务器IP |
| 后端 API | http://你的服务器IP:8000 |
| API 文档 | http://你的服务器IP/docs |
| 健康检查 | http://你的服务器IP/api/health |

---

## 常用运维命令

```bash
cd /www/wwwroot/exam-site

# 启动
docker compose up -d

# 停止
docker compose down

# 重启
docker compose restart

# 重新构建（代码更新后）
docker compose up -d --build

# 查看实时日志
docker compose logs -f

# 查看后端日志
docker logs -f exam-backend

# 进入容器调试
docker exec -it exam-backend bash

# 更新文档后重建索引（重启后端即可）
docker compose restart backend

# 完全清除重建
docker compose down -v
docker compose up -d --build
```

---

## 宝塔防火墙配置

宝塔面板 → 安全 → 防火墙：

| 端口 | 协议 | 说明 |
|------|------|------|
| 80 | TCP | 前端访问（必须放行） |
| 8000 | TCP | 后端调试（可选，建议仅内网） |

---

## 宝塔反向代理配置（可选）

如果不想直接暴露 8000 端口，可以用宝塔反向代理：

1. 宝塔面板 → 网站 → 添加站点 → 输入域名
2. 站点设置 → 反向代理
3. 添加代理：
   - 代理名称：`exam-api`
   - 目标 URL：`http://127.0.0.1:8000`
   - 发送域名：`$host`
4. 这样前端直接通过 80 端口访问，API 也通过 80 端口的 `/api/` 路径访问

如果使用反向代理，可修改 `docker-compose.yml`，将 backend 的 `ports: "8000:8000"` 去掉，只保留内部网络通信。

---

## 故障排查

### 容器启动失败

```bash
# 查看详细错误
docker compose logs

# 单独构建后端排查
cd backend
docker build -t exam-backend .
docker run --rm exam-backend python -c "from app.main import app; print('OK')"
```

### RAG 索引构建失败

```bash
# 检查 doc/ 目录是否存在
docker exec exam-backend ls /doc

# 检查文档解析
docker exec exam-backend python -c "
from app.services.document_parser import load_all_documents
chunks = load_all_documents('/doc')
print(f'Parsed {len(chunks)} chunks')
"
```

### API 调用超时

编辑 `.env`，增大超时时间：
```env
OPENAI_TIMEOUT_SECONDS=60
```
然后重启：
```bash
docker compose up -d --build
```

### 内存不足

在 `docker-compose.yml` 中添加内存限制：
```yaml
backend:
  deploy:
    resources:
      limits:
        memory: 512M
```
