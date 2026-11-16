FROM python:3.11-slim

WORKDIR /app

# 设置环境变量，防止生成 .pyc 缓存并确保日志实时输出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["pytest", "--alluredir=./allure-results"]