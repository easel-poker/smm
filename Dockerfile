FROM debian:bullseye-slim

# نصب وابستگی‌های لازم، مرورگر رسمی Google Chrome و نمایشگر مجازی Xvfb
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    xvfb \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    xdg-utils \
    --no-install-recommends \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN chmod +x start.sh

# اجرای کروم واقعی ۲۴ ساعته همراه با اکستنشن اختصاصی
CMD ["bash", "start.sh"]
