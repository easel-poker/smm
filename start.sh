#!/bin/bash

echo "🚀 Starting Virtual Display (Xvfb)..."
Xvfb :99 -screen 0 1920x1080x24 -ac &
export DISPLAY=:99
sleep 2

# حلقه اجرای دائمی کروم (اگر کروم بسته شد خودکار ریستارت شود)
while true; do
  echo "🌐 Launching Google Chrome with OneSMM Extension..."
  google-chrome-stable \
    --no-sandbox \
    --disable-gpu \
    --disable-dev-shm-usage \
    --disable-software-rasterizer \
    --load-extension=/app/extension \
    --disable-extensions-except=/app/extension \
    --user-data-dir=/app/chrome_profile \
    --no-first-run \
    --no-default-browser-check \
    --start-maximized \
    "https://onesmm.com/signup"
  
  echo "⚠️ Chrome process stopped, restarting in 3 seconds..."
  sleep 3
done
