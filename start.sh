#!/bin/bash

# غیرفعال‌سازی هشدارهای D-Bus در داکر لینوکس
export NO_AT_BRIDGE=1
export DBUS_SESSION_BUS_ADDRESS=/dev/null

echo "🚀 Starting Virtual Display (Xvfb)..."
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99
sleep 2

echo "🌐 Google Chrome is starting on Railway..."

# اجرای پایدار کروم در کانتینر
while true; do
  google-chrome-stable \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --disable-software-rasterizer \
    --disable-background-networking \
    --disable-default-apps \
    --disable-sync \
    --load-extension=/app/extension \
    --disable-extensions-except=/app/extension \
    --user-data-dir=/app/chrome_profile \
    --no-first-run \
    --no-default-browser-check \
    --start-maximized \
    "https://onesmm.com/signup"
  
  echo "⚠️ Chrome process restarted..."
  sleep 3
done
