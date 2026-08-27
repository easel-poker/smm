#!/bin/bash

echo "🚀 Starting Virtual Display (Xvfb)..."
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

echo "🌐 Launching Google Chrome with OneSMM Extension..."
# اجرای کروم با لود خودکار اکستنشن (دقیقاً همان منطق تمپرمونکی)
google-chrome-stable \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --load-extension=/app/extension \
  --disable-extensions-except=/app/extension \
  --user-data-dir=/app/chrome_profile \
  --no-first-run \
  --no-default-browser-check \
  --start-maximized \
  "https://onesmm.com/signup"
