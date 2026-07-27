# 宝塔部署步骤

## 前置：把最新代码推送到服务器

传最新代码到服务器（确保包含以下新增文件）：
- exam-site/docker-compose.yml
- exam-site/backend/Dockerfile
- exam-site/backend/app/services/document_parser.py
- exam-site/backend/app/services/embedding_service.py
- exam-site/backend/app/services/rag_service.py
- exam-site/frontend/src/components/ChatWidget.tsx
- exam-site/.env（填好 API Key）

---

## 第一步：修改 .env 配置

编辑 `/www/wwwroot/exam-site/.env`：
```env
OPENAI_API_KEY=你的API_Key
OPENAI_MODEL=step-3.7-flash
OPENAI_BASE_URL=https://api.stepfun.com/step_plan/v1
OPENAI_TIMEOUT_SECONDS=30
```

---

## 第二步：启动后端 Docker 容器

```bash
cd /www/wwwroot/exam-site
docker compose up -d --build
```

这只会启动后端容器（端口 8000），前端走宝塔 Nginx 托管 dist。

---

## 第三步：宝塔 Nginx 配置

宝塔面板 → 网站 → 点击你的站点 → 配置文件，替换为：

```nginx
server {
    listen 80;
    server_name 你的域名或IP;
    root /www/wwwroot/exam-site/frontend/dist;
    index index.html;

    # 前端 SPA
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理到 Docker 后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # 静态资源缓存
    location /assets/ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 第四步：构建前端

前端 dist 目录需要先在本地构建好再上传，或者从 Docker 弄出来：

```bash
cd /www/wwwroot/exam-site/frontend
docker run --rm -v "$(pwd):/build" -w /build node:20-alpine sh -c "npm install --registry=https://registry.npmmirror.com && npm run build"
```

执行完这步后，`frontend/dist/` 目录就有了构建好的前端文件。

---

## 第五步：验证

```bash
# 检查后端容器
docker compose ps

# 检查后端 API
curl http://127.0.0.1:8000/api/health

# 检查前端
curl http://127.0.0.1/
```

访问 `http://你的IP/` 看前端，访问 `http://你的IP/docs` 看 API 文档。

---

## 后续更新流程

```bash
cd /www/wwwroot/exam-site

# 拉最新代码
git pull

# 重新构建后端
docker compose up -d --build

# 重新构建前端
cd frontend
docker run --rm -v "$(pwd):/build" -w /build node:20-alpine sh -c "npm install --registry=https://registry.npmmirror.com && npm run build"
```
