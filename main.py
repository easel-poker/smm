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
LOGOUT_DELAY_SEC   = 3
# ───────────────────────────────────────────────────────────────

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
    print("🤖 شنود تلگرام فعال است...")
    send_tg_msg("🚀 *ربات OneSMM در Railway با موفقیت راه‌اندازی شد!*\nچرخه خودکار آماده است.")

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
                        send_tg_msg(f"🚀 *چرخه خودکار فعال شد!*")

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
    first_names = ["alex", "daniel", "david", "ryan", "kevin", "eric", "brian", "sarah", "olivia", "noah", "mason", "lucas", "ethan", "james", "logan", "liam", "adam", "ben"]
    last_names = ["miller", "smith", "williams", "brown", "jones", "garcia", "davis", "wilson", "clark", "taylor", "anderson", "white", "jackson", "harris"]
    fn = random.choice(first_names)
    ln = random.choice(last_names)
    num = random.randint(100, 999)
    username = f"{fn}_{ln}{num}"
    email = f"{fn}.{ln}{random.randint(1000, 99990)}@gmail.com"
    password = "Pass@" + "".join(random.choices(string.ascii_letters + string.digits, k=8)) + "9!"
    return username, email, password


def browser_worker():
    global is_running, current_accounts, total_created_count, current_proxy_idx

    with sync_playwright() as p:
        while True:
            if not is_running:
                time.sleep(2)
                continue

            proxy = PROXIES[current_proxy_idx % len(PROXIES)]
            print(f"\n[+] باز کردن مرورگر با پروکسی: {proxy['country']} ({proxy['server']})")

            browser = None
            context = None
            page = None
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
                        "--disable-infobars",
                        "--window-size=1920,1080"
                    ]
                )

                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    locale="en-US",
                    timezone_id="America/New_York"
                )

                # اسکریپت ضدتشخیص
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
                    Object.defineProperty(document, 'hidden', { get: () => false, configurable: true });
                    Object.defineProperty(document, 'visibilityState', { get: () => 'visible', configurable: true });
                    Document.prototype.hasFocus = () => true;
                    document.hasFocus = () => true;
                """)

                page = context.new_page()
                page.set_default_timeout(20000)  # حداکثر ۲۰ ثانیه تایم‌اوت به جای ۴۵ ثانیه برای سرعت بیشتر
                username, email, password = generate_credentials()

                print(f"[+] ورود به صفحه ثبت‌نام OneSMM...")
                page.goto(SIGNUP_URL, wait_until="domcontentloaded", timeout=20000)
                time.sleep(1.5)

                # ۱. کلیک روی تب Sign up و پر کردن فیلدها
                signup_tab = page.locator("#auth-tab-signup, a:has-text('Sign up'), button:has-text('Sign up')").first
                if signup_tab.count() > 0:
                    try:
                        signup_tab.click(timeout=2000)
                    except Exception:
                        pass

                # پر کردن دقیق با رویدادهای استاندارد
                page.evaluate("""({u, e, p}) => {
                    const setNativeValue = (el, val) => {
                        if (!el) return;
                        el.focus();
                        const valueSetter = Object.getOwnPropertyDescriptor(el, 'value')?.set;
                        const prototype = Object.getPrototypeOf(el);
                        const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;
                        if (prototypeValueSetter && valueSetter !== prototypeValueSetter) {
                            prototypeValueSetter.call(el, val);
                        } else if (valueSetter) {
                            valueSetter.call(el, val);
                        } else {
                            el.value = val;
                        }
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        el.dispatchEvent(new Event('blur', { bubbles: true }));
                    };

                    const passInputs = document.querySelectorAll("#auth-panel-signup input[type='password'], form input[type='password'], input[type='password']");
                    const uField = document.querySelector("#login") || document.querySelector("input[name='login']") || document.querySelector("input[name='username']");
                    const eField = document.querySelector("#email") || document.querySelector("input[name='email']") || document.querySelector("input[type='email']");
                    const pField = document.querySelector("#password") || document.querySelector("input[name='password']") || passInputs[0];
                    const cField = document.querySelector("#password_again") || document.querySelector("input[name='password_again']") || passInputs[1];

                    setNativeValue(uField, u);
                    setNativeValue(eField, e);
                    setNativeValue(pField, p);
                    setNativeValue(cField, p);
                }""", {"u": username, "e": email, "p": password})

                time.sleep(1.0)

                # ۲. کلیک واقعی ماوس روی دکمه Sign up برای احضار کپچا
                print(f"[+] کلیک روی دکمه Sign up...")
                submit_btn = page.locator("#auth-panel-signup button.auth-submit, #auth-panel-signup button[type='submit'], button.auth-submit, button:has-text('Sign up')").first
                if submit_btn.count() > 0:
                    submit_btn.click(timeout=3000)
                else:
                    page.evaluate("() => document.querySelector('button[type=\"submit\"]').click()")

                # ۳. کلیک واقعی ماوس (Trusted Click) روی تیک hCaptcha در تمام فریم‌ها
                print(f"[+] در حال کلیک واقعی روی تیک کپچا...")
                captcha_solved = False
                for _ in range(25):
                    for frame in page.frames:
                        if "hcaptcha.com" in frame.url.lower():
                            try:
                                cb = frame.locator("#checkbox, #anchor, [role='checkbox']").first
                                if cb.count() > 0 and cb.is_visible():
                                    cb.click(timeout=2000)
                            except Exception:
                                pass

                    # بررسی مقداردهی توکن حل شده
                    try:
                        token_len = page.evaluate("""() => {
                            const resp = document.querySelector("[name='h-captcha-response'], [name='g-recaptcha-response']");
                            return resp ? (resp.value || '').trim().length : 0;
                        }""")
                        if token_len > 10:
                            captcha_solved = True
                            print(f"[✓] تیک کپچا با موفقیت تایید شد!")
                            break
                    except Exception:
                        pass

                    time.sleep(0.8)

                # ۴. بررسی ورود به پنل و داشبورد اکانت
                print(f"[+] در حال بررسی ورود به داشبورد اکانت...")
                logged_in = False
                for _ in range(20):
                    is_logged = page.evaluate("""() => {
                        return document.querySelector("a[href*='/logout'], a[href*='logout'], a[href*='signout'], .user-avatar, .account-balance, a[href*='/orders']") !== null;
                    }""")
                    if is_logged:
                        logged_in = True
                        break
                    time.sleep(0.6)

                # ۵. تاخیر ۳ ثانیه‌ای برای لود کامل اکانت
                if logged_in:
                    print(f"[+] اکانت با موفقیت لود شد. انتظار {LOGOUT_DELAY_SEC} ثانیه...")
                    time.sleep(LOGOUT_DELAY_SEC)

                    with lock:
                        current_accounts.append({
                            "username": username,
                            "email": email,
                            "password": password
                        })
                        total_created_count += 1

                    # ارسال پیام موفقیت به تلگرام
                    send_tg_msg(
                        f"👤 *اکانت جدید ساخته شد ({len(current_accounts)}/{BATCH_SIZE}):*\n"
                        f"🌍 پروکسی: {proxy['country']}\n"
                        f"Username: `{username}`\n"
                        f"Email: `{email}`\n"
                        f"Password: `{password}`"
                    )
                    print(f"[✓] اکانت {username} ذخیره شد.")

                    # ارسال پکیج ۲۵ تایی و تغییر پروکسی
                    if len(current_accounts) >= BATCH_SIZE:
                        next_p = PROXIES[(current_proxy_idx + 1) % len(PROXIES)]["country"]
                        send_tg_file(
                            current_accounts,
                            f"🎁 *پکیج {BATCH_SIZE} تایی تکمیل و ارسال شد!*\n🔄 حافظه ریست شد.\n🌐 پروکسی بعدی ➔ {next_p}"
                        )
                        with lock:
                            current_accounts.clear()
                        current_proxy_idx += 1

                else:
                    print(f"[!] ورود تایید نشد (احتمالاً به دلیل کپچا تصویری در این پروکسی). سوئیچ به پروکسی بعدی...")
                    try:
                        scr = page.screenshot()
                        send_tg_photo(scr, f"⚠️ *عدم ورود:* کپچا یا پروکسی {proxy['country']} رد نشد. در حال تست پروکسی بعدی...")
                    except Exception:
                        pass
                    current_proxy_idx += 1

            except Exception as e:
                print(f"[!] خطا: {e}")
                try:
                    if page:
                        scr = page.screenshot()
                        send_tg_photo(scr, f"⚠️ *خطا در سرور:* `{str(e)[:100]}`\nپروکسی: {proxy['country']}")
                except Exception:
                    send_tg_msg(f"⚠️ *خطای پروکسی {proxy['country']}:* `{str(e)[:100]}`\nدر حال رفتن به پروکسی بعدی...")
                current_proxy_idx += 1

            finally:
                if context:
                    try:
                        context.close()
                    except Exception:
                        pass
                if browser:
                    try:
                        browser.close()
                    except Exception:
                        pass
                time.sleep(random.uniform(1.5, 3.0))


if __name__ == "__main__":
    tg_thread = threading.Thread(target=telegram_listener, daemon=True)
    tg_thread.start()

    browser_worker()
