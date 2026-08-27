FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# نصب ابزارهای نمایشگر مجازی و اسکرین‌شات
RUN apt-get update && apt-get install -y \
    xvfb \
    scrot \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
