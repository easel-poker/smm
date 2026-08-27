FROM debian:bookworm-slim

# نصب گوگل کروم رسمی و ابزار مانیتور مجازی (Xvfb)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    ca-certificates \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# کپی افزونه و اسکریپت اجرا
COPY extension /app/extension
COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
