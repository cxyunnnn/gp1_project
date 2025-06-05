FROM --platform=linux/amd64 python:3.14-rc-slim

RUN apt update

# Create a working directory
WORKDIR /app

# Copy the requirements file into the image
COPY requirements.txt /app/
COPY gp1_project_web.py /app/
# 如果要在啟動container時設定系統環境變數，可以不用複製.env檔案
COPY .env /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8080

# Set the entrypoint for the container
ENTRYPOINT ["python", "gp1_project_web.py"]