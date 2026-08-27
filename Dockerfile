FROM python:3.11-slim

# نصب پکیج‌های ضروری لینوکس، نمایشگر مجازی Xvfb و ابزار اسکرین‌شات scrot
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    xvfb \
    scrot \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    xdg-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps chromium

COPY . .

CMD ["python", "main.py"]
