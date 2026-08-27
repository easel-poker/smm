import os
import sys
import time
import json
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

# ─── تنظیمات تلگرام و پکیج ──────────────────────────────────────
TELEGRAM_BOT_TOKEN = "8889364969:AAGqjYvQgSxvTivPQaa4vJSELgRpDYDajzs"
TELEGRAM_CHAT_ID   = "8496696077"
BATCH_SIZE         = 25
LOCAL_SERVER_PORT  = 5000
# ───────────────────────────────────────────────────────────────

is_running = True
current_accounts = []
total_created_count = 0
last_update_id = 0
lock = threading.Lock()


def send_tg_msg(text):
    try:
        keyboard = {
            "keyboard": [
                [{"text": "▶️ شروع چرخه"}, {"text": "⏹️ توقف چرخه"}],
                [{"text": "📊 وضعیت"}, {"text": "📸 عکس از صفحه"}],
                [{"text": "💾 دریافت فایل اکانت‌ها"}, {"text": "🗑️ ریست حافظه"}]
            ],
            "resize_keyboard": True
        }
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        }, timeout=10)
    except Exception as e:
        print(f"[!] Telegram send error: {e}")


def send_tg_photo(image_bytes, caption):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        files = {"photo": ("screenshot.png", image_bytes, "image/png")}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}
        requests.post(url, data=data, files=files, timeout=20)
    except Exception as e:
        print(f"[!] Telegram photo error: {e}")


def send_tg_file(accounts_list, caption):
    try:
        filename = f"onesmm_accounts_{len(accounts_list)}_{int(time.time())}.txt"
        file_text = f"=== لیست {len(accounts_list)} اکانت ثبت‌شده OneSMM ===\n"
        file_text += f"تاریخ: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for i, acc in enumerate(accounts_list, 1):
            file_text += f"[{i}] Username: {acc['username']}\nEmail: {acc['email']}\nPassword: {acc['password']}\n-----------------------------------\n"

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        files = {"document": (filename, file_text.encode('utf-8'), "text/plain")}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}
        requests.post(url, data=data, files=files, timeout=25)
    except Exception as e:
        print(f"[!] Telegram file send error: {e}")


class ExtensionWebhookHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        global is_running
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {
            "status": "ok",
            "is_running": is_running,
            "accounts_count": len(current_accounts),
            "batch_size": BATCH_SIZE
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        global current_accounts, total_created_count

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
            username = data.get("username", "")
            email = data.get("email", "")
            password = data.get("password", "")

            with lock:
                current_accounts.append({
                    "username": username,
                    "email": email,
                    "password": password,
                    "time": time.strftime('%Y-%m-%d %H:%M:%S')
                })
                total_created_count += 1
                count = len(current_accounts)

            print(f"[✓] اکانت جدید دریافت شد: {username}")

            send_tg_msg(
                f"👤 *اکانت جدید ساخته شد ({count}/{BATCH_SIZE}):*\n"
                f"Username: `{username}`\n"
                f"Email: `{email}`\n"
                f"Password: `{password}`"
            )

            if count >= BATCH_SIZE:
                with lock:
                    batch_to_send = list(current_accounts)
                    current_accounts.clear()

                send_tg_file(
                    batch_to_send,
                    f"🎁 *پکیج {BATCH_SIZE} تایی تکمیل و ارسال شد!*\n🔄 حافظه ریست شد."
                )

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status":"saved"}')

        except Exception as e:
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        return


def run_local_api_server():
    server = HTTPServer(('0.0.0.0', LOCAL_SERVER_PORT), ExtensionWebhookHandler)
    server.serve_forever()


def telegram_listener():
    global is_running, last_update_id, current_accounts
    send_tg_msg("🚀 *ربات تلگرام در Railway فعال شد!*")

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=5"
            res = requests.get(url, timeout=10).json()

            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    sender_id = str(msg.get("chat", {}).get("id", ""))
                    text = msg.get("text", "").strip()

                    if sender_id != TELEGRAM_CHAT_ID:
                        continue

                    if text in ["/start", "▶️ شروع چرخه"]:
                        with lock:
                            is_running = True
                        send_tg_msg(f"🚀 *چرخه ساخت اکانت فعال شد!*")

                    elif text in ["/stop", "⏹️ توقف چرخه"]:
                        with lock:
                            is_running = False
                        send_tg_msg(f"⏹️ *چرخه ساخت اکانت متوقف شد.*")

                    elif text in ["/screenshot", "📸 عکس از صفحه"]:
                        os.system("DISPLAY=:99 scrot -o /tmp/screen.png")
                        if os.path.exists("/tmp/screen.png"):
                            try:
                                with open("/tmp/screen.png", "rb") as f:
                                    send_tg_photo(f.read(), "📸 *تصویر زنده از صفحه نمایش کروم در Railway*")
                            except Exception:
                                send_tg_msg("⚠️ خطای خواندن تصویر اسکرین‌شات.")
                        else:
                            send_tg_msg("⚠️ تصویری یافت نشد.")

                    elif text in ["/status", "📊 وضعیت"]:
                        status_str = "🟢 در حال ساخت" if is_running else "🔴 متوقف"
                        send_tg_msg(
                            f"📊 *وضعیت زنده ربات در Railway:*\n"
                            f"• وضعیت چرخه: {status_str}\n"
                            f"• پیشرفت پکیج جاری: *{len(current_accounts)} از {BATCH_SIZE} عدد*\n"
                            f"• مجموع کل اکانت‌های ساخته‌شده: *{total_created_count} عدد*"
                        )

                    elif text in ["/export", "💾 دریافت فایل اکانت‌ها"]:
                        with lock:
                            acc_len = len(current_accounts)
                            acc_copy = list(current_accounts)

                        if acc_len == 0:
                            send_tg_msg("⚠️ هنوز اکانتی در پکیج جاری ساخته نشده است!")
                        else:
                            send_tg_file(acc_copy, f"💾 خروجی دستی ({acc_len} اکانت)")

                    elif text in ["/reset", "🗑️ ریست حافظه"]:
                        with lock:
                            current_accounts.clear()
                        send_tg_msg("🗑️ *حافظه پکیج جاری صفر شد.*")

        except Exception as e:
            time.sleep(2)

        time.sleep(1)


def start_chrome_supervisor():
    os.system("Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &")
    os.environ["DISPLAY"] = ":99"
    time.sleep(2)

    chrome_cmd = [
        "google-chrome-stable",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--load-extension=/app/extension",
        "--user-data-dir=/app/chrome_profile",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1920,1080",
        "--start-maximized",
        "https://onesmm.com/signup"
    ]

    while True:
        try:
            proc = subprocess.Popen(chrome_cmd)
            proc.wait()
        except Exception as e:
            pass
        time.sleep(3)


if __name__ == "__main__":
    threading.Thread(target=run_local_api_server, daemon=True).start()
    threading.Thread(target=telegram_listener, daemon=True).start()
    start_chrome_supervisor()
