import os
import sys
import time
import random
import string
import threading
import requests
from playwright.sync_api import sync_playwright

# ─── تنظیمات تلگرام و سقف پکیج ──────────────────────────────────
TELEGRAM_BOT_TOKEN = "8889364969:AAGqjYvQgSxvTivPQaa4vJSELgRpDYDajzs"
TELEGRAM_CHAT_ID   = "8496696077"
BATCH_SIZE         = 25
SIGNUP_URL         = "https://onesmm.com/signup"
# ───────────────────────────────────────────────────────────────

# لیست ۱۰ پروکسی Webshare شما (برای جلوگیری از مسدود شدن آی‌پی دیتاسنتر Railway)
PROXIES = [
    {"server": "http://31.59.20.176:6754",   "username": "dprcdrqc", "password": "tbzxenvozzvm", "country": "UK 🇬🇧"},
    {"server": "http://45.38.107.97:6014",   "username": "dprcdrqc", "password": "tbzxenvozzvm", "country": "UK 🇬🇧"},
    {"server": "http://198.105.121.200:6462", "username": "dprcdrqc", "password": "tbzxenvozzvm", "country": "UK 🇬🇧"},
    {"server": "http://64.137.96.74:6641",   "username": "dprcdrqc", "password": "tbzxenvozzvm", "country": "Spain 🇪🇸"},
    {"server": "http://198.23.243.226:6361", "username": "dprcdrqc", "password": "tbzxenvozzvm", "country": "US 🇺🇸"},
    {"server": "http://38.154.185.97:6370",  "username": "dprcdrqc", "password": "tbzxenvozzvm", "country": "US 🇺🇸"},
    {"server": "http://84.247.60.125:6095",  "username": "dprcdrqc", "password": "tbzxenvozzvm", "country": "Poland 🇵🇱"},
    {"server": "http://142.111.67.146:5611", "username": "dprcdrqc", "password": "tbzxenvozzvm", "country": "Japan 🇯🇵"},
    {"server": "http://191.96.254.138:6185", "username": "dprcdrqc", "password": "tbzxenvozzvm", "country": "US 🇺🇸"},
    {"server": "http://31.58.9.4:6077",      "username": "dprcdrqc", "password": "tbzxenvozzvm", "country": "Germany 🇩🇪"},
]

is_running = True
current_accounts = []
total_created_count = 0
last_update_id = 0
lock = threading.Lock()
current_proxy_idx = 0


def send_tg_msg(text):
    try:
        keyboard = {
            "keyboard": [
                [{"text": "▶️ شروع چرخه"}, {"text": "⏹️ توقف چرخه"}],
                [{"text": "📊 وضعیت"}, {"text": "💾 دریافت فایل اکانت‌ها"}],
                [{"text": "🗑️ ریست حافظه"}]
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
    """ارسال اسکرین‌شات از وضعیت مرورگر به تلگرام برای عیب‌یابی"""
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


def telegram_listener():
    global is_running, last_update_id, current_accounts
    print("🤖 شنود دستورات تلگرام فعال است...")

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

                    print(f"📩 دستور دریافتی: {text}")

                    if text in ["/start", "▶️ شروع چرخه"]:
                        with lock:
                            is_running = True
                        send_tg_msg(f"🚀 *چرخه خودکار فعال شد!*\nمرورگر با پروکسی فعال شد...")

                    elif text in ["/stop", "⏹️ توقف چرخه"]:
                        with lock:
                            is_running = False
                        send_tg_msg(f"⏹️ *چرخه خودکار متوقف شد.*\nپیشرفت فعلی: *{len(current_accounts)} / {BATCH_SIZE}*")

                    elif text in ["/status", "📊 وضعیت"]:
                        status_str = "🟢 در حال ساخت" if is_running else "🔴 متوقف"
                        proxy_info = PROXIES[current_proxy_idx % len(PROXIES)]["country"]
                        send_tg_msg(
                            f"📊 *وضعیت زنده ربات در Railway:*\n"
                            f"• وضعیت چرخه: {status_str}\n"
                            f"• پروکسی جاری: {proxy_info}\n"
                            f"• پیشرفت پکیج جاری: *{len(current_accounts)} از {BATCH_SIZE} عدد*\n"
                            f"• مجموع کل اکانت‌های ساخته‌شده: *{total_created_count} عدد*"
                        )

                    elif text in ["/export", "💾 دریافت فایل اکانت‌ها"]:
                        if len(current_accounts) == 0:
                            send_tg_msg("⚠️ هنوز اکانتی در پکیج جاری ساخته نشده است!")
                        else:
                            send_tg_file(current_accounts, f"💾 خروجی دستی ({len(current_accounts)} اکانت)")

                    elif text in ["/reset", "🗑️ ریست حافظه"]:
                        with lock:
                            current_accounts.clear()
                        send_tg_msg("🗑️ *حافظه پکیج جاری صفر شد.*")

        except Exception as e:
            time.sleep(2)

        time.sleep(1)


def generate_credentials():
    first_names = ["alex", "daniel", "david", "ryan", "kevin", "eric", "brian", "sarah", "olivia", "noah", "mason", "lucas", "ethan", "james", "logan", "liam"]
    last_names = ["miller", "smith", "williams", "brown", "jones", "garcia", "davis", "wilson", "clark", "taylor", "anderson", "white", "jackson"]
    fn = random.choice(first_names)
    ln = random.choice(last_names)
    num = random.randint(100, 999)
    username = f"{fn}_{ln}{num}"
    email = f"{fn}.{ln}{random.randint(1000, 9999)}@gmail.com"
    password = "Pass@" + "".join(random.choices(string.ascii_letters + string.digits, k=8)) + "1!"
    return username, email, password


def browser_worker():
    global is_running, current_accounts, total_created_count, current_proxy_idx

    print("🌐 راه‌اندازی مرورگر به همراه شبکه پروکسی...")

    with sync_playwright() as p:
        while True:
            if not is_running:
                time.sleep(2)
                continue

            proxy = PROXIES[current_proxy_idx % len(PROXIES)]
            print(f"\n" + "="*50)
            print(f"🌍 اتصال از طریق پروکسی: {proxy['country']} ({proxy['server']})")
            print("="*50)

            try:
                browser = p.chromium.launch(
                    headless=True,
                    proxy={
                        "server": proxy["server"],
                        "username": proxy["username"],
                        "password": proxy["password"]
                    },
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--window-size=1920,1080"
                    ]
                )
            except Exception as e:
                print(f"[!] خطای اجرای مرورگر با پروکسی: {e}")
                current_proxy_idx += 1
                time.sleep(3)
                continue

            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )

            # بایپس ضدربات
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
            """)

            page = context.new_page()
            username, email, password = generate_credentials()

            try:
                print(f"[+] در حال باز کردن سایت OneSMM برای اکانت: {username}...")
                page.goto(SIGNUP_URL, wait_until="domcontentloaded", timeout=45000)
                time.sleep(2.0)

                # تب Sign up
                signup_tab = page.locator("#auth-tab-signup")
                if signup_tab.is_visible():
                    signup_tab.click()
                    time.sleep(0.8)

                # پر کردن فرم
                page.locator("#login").fill(username)
                page.locator("#email").fill(email)
                page.locator("#password").fill(password)
                page.locator("#password_again").fill(password)
                time.sleep(0.8)

                # کلیک ثبت‌نام
                submit_btn = page.locator("#auth-panel-signup button.auth-submit, button.auth-submit").first
                submit_btn.click()
                print(f"[+] فرم ارسال شد، در حال تیک زدن کپچا...")

                # کلیک خودکار روی تیک کپچا
                time.sleep(2.0)
                captcha_clicked = False
                for _ in range(15):
                    for frame in page.frames:
                        if "hcaptcha.com" in frame.url.lower():
                            try:
                                cb = frame.locator('#checkbox, div#anchor, [role="checkbox"]').first
                                if cb.is_visible():
                                    cb.click()
                                    captcha_clicked = True
                                    print("[+] تیک کپچا فشرده شد.")
                                    break
                            except Exception:
                                pass
                    if captcha_clicked:
                        break
                    time.sleep(1.0)

                time.sleep(6.0)

                with lock:
                    current_accounts.append({
                        "username": username,
                        "email": email,
                        "password": password
                    })
                    total_created_count += 1

                # ارسال اعلان زنده به تلگرام
                send_tg_msg(
                    f"👤 *اکانت جدید ساخته شد ({len(current_accounts)}/{BATCH_SIZE}):*\n"
                    f"🌍 کشور: {proxy['country']}\n"
                    f"Username: `{username}`\n"
                    f"Email: `{email}`\n"
                    f"Password: `{password}`"
                )
                print(f"[✓] اکانت ساخته شد ({len(current_accounts)}/{BATCH_SIZE})")

                # اگر به ۲۵ رسید -> ارسال فایل و تغییر پروکسی
                if len(current_accounts) >= BATCH_SIZE:
                    next_proxy = PROXIES[(current_proxy_idx + 1) % len(PROXIES)]["country"]
                    send_tg_file(
                        current_accounts,
                        f"🎁 *پکیج ۲۵ تایی اکانت‌ها با موفقیت تکمیل و ارسال شد!*\n🔄 حافظه ریست شد.\n🌐 پروکسی بعدی ➔ {next_proxy}"
                    )
                    with lock:
                        current_accounts.clear()
                    current_proxy_idx += 1

            except Exception as e:
                print(f"[!] خطا در ثبت‌نام: {e}")
                # ارسال عکس صفحه و علت به تلگرام برای عیب‌یابی دقیق
                try:
                    scr = page.screenshot()
                    send_tg_photo(scr, f"⚠️ *خطا در ساخت اکانت:*\n`{str(e)[:150]}`\nپروکسی بعدی تست می‌شود...")
                except Exception:
                    pass
                current_proxy_idx += 1  # تست پروکسی بعدی

            finally:
                context.close()
                browser.close()
                time.sleep(random.uniform(3.0, 6.0))


if __name__ == "__main__":
    tg_thread = threading.Thread(target=telegram_listener, daemon=True)
    tg_thread.start()

    browser_worker()
