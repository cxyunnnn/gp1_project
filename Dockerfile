# 使用穩定正式版 Python
FROM python:3.12-slim

# 更新套件來源並安裝必要套件（可視需要擴充）
RUN apt update && apt install -y --no-install-recommends \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

# 建立工作目錄
WORKDIR /app

# 複製專案檔案進入 image
COPY requirements.txt .
COPY gp1_project_web.py .
COPY .env .

# 安裝 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 開放容器的 8080 port
EXPOSE 8080

# 執行入口
ENTRYPOINT ["python", "gp1_project_web.py"]
