# 使用Python 3.11作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV FLASK_APP=src/web/web_ui.py
ENV FLASK_ENV=production

# 安装系统依赖（使用默认源，如果失败则尝试国内镜像）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    netcat-openbsd \
    || (echo "deb http://mirrors.aliyun.com/debian/ bookworm main contrib non-free" > /etc/apt/sources.list \
        && echo "deb http://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free" >> /etc/apt/sources.list \
        && echo "deb http://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list \
        && apt-get update && apt-get install -y gcc g++ curl wget netcat-openbsd) \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p uploads data/exports logs volumes

# 设置权限
RUN chmod +x start.py docker-entrypoint.sh

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# 使用入口脚本
ENTRYPOINT ["./docker-entrypoint.sh"] 