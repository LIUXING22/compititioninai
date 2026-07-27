# 前端纯构建——不运行 Nginx
# 宝塔宿主机 Nginx 直接托管 dist/ 目录
FROM node:20-alpine AS builder

WORKDIR /build

COPY package*.json ./
RUN npm ci --registry=https://registry.npmmirror.com

COPY . .
RUN npm run build
