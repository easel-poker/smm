// ─── تنظیمات اختصاصی تلگرام شما ───────────────────────────
const TELEGRAM_BOT_TOKEN = "8889364969:AAGqjYvQgSxvTivPQaa4vJSELgRpDYDajzs";
const TELEGRAM_CHAT_ID   = "8496696077";
const BATCH_SIZE         = 25; // ارسال فایل و ریست هر ۲۵ اکانت
// ──────────────────────────────────────────────────────────

(function() {
    'use strict';

    let lastUpdateId = parseInt(localStorage.getItem("tg_last_update_id") || "0");

    // ۱. کلیک خودکار روی تیک داخل فریم hCaptcha
    if (window.location.hostname.includes("hcaptcha.com")) {
        const checkCaptcha = setInterval(() => {
            const cb = document.querySelector("#checkbox") || 
                       document.querySelector("#anchor") || 
                       document.querySelector("[role='checkbox']");

            if (cb && cb.offsetParent !== null) {
                clearInterval(checkCaptcha);
                setTimeout(() => {
                    cb.click();
                    console.log("🎯 تیک کپچا فشرده شد!");
                }, 600);
            }
        }, 300);

        setTimeout(() => clearInterval(checkCaptcha), 15000);
        return;
    }

    // ۲. چرخه ثبت‌نام و مدیریت هوشمند تلگرام
    if (window.location.hostname.includes("onesmm.com")) {
        const path = window.location.pathname.toLowerCase();
        createControlPanel();

        // ارسال پیام اعلان روشن شدن سرور برای بار اول
        if (!sessionStorage.getItem("railway_startup_notified")) {
            sessionStorage.setItem("railway_startup_notified", "true");
            sendTelegramMessage("🟢 *ربات با موفقیت در Railway روشن شد و آماده دریافت دستورات است!*");
        }

        // پایش پیوسته پیام‌های تلگرام هر ۲ ثانیه
        setInterval(pollTelegramCommands, 2000);

        const isLoopActive = localStorage.getItem("onesmm_loop_active") === "true";
        if (!isLoopActive) return;

        window.addEventListener('load', function() {
            if (path.includes("/signup") || path.includes("/register")) {
                setPanelStatus("✍️ در حال پر کردن فرم...");
                setTimeout(runRegistrationFlow, 1000);
            }
            else if (isUserActuallyLoggedIn()) {
                setPanelStatus("🎉 ثبت‌نام موفق! در حال خروج...");
                setTimeout(() => {
                    setPanelStatus("🚪 خروج...");
                    const logoutBtn = document.querySelector("a[href*='logout']");
                    if (logoutBtn) {
                        logoutBtn.click();
                    } else {
                        window.location.replace("https://onesmm.com/logout");
                    }
                }, 2500);
            }
            else {
                setPanelStatus("🔄 بازگشت به صفحه ثبت‌نام...");
                setTimeout(() => {
                    window.location.replace("https://onesmm.com/signup");
                }, 1200);
            }
        });
    }

    function isUserActuallyLoggedIn() {
        return document.querySelector("a[href*='/logout'], a[href*='logout'], a[href*='signout']") !== null;
    }

    // دریافت دستورات از تلگرام
    async function pollTelegramCommands() {
        try {
            const res = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates?offset=${lastUpdateId + 1}&timeout=1`);
            const data = await res.json();
            if (!data || !data.ok || !data.result) return;

            for (const update of data.result) {
                lastUpdateId = update.update_id;
                localStorage.setItem("tg_last_update_id", lastUpdateId.toString());

                const msg = update.message || update.callback_query?.message;
                const text = update.message?.text || update.callback_query?.data || "";
                const senderId = (msg?.chat?.id || "").toString();

                if (senderId !== TELEGRAM_CHAT_ID.toString()) continue;

                handleTelegramCommand(text.trim());
            }
        } catch (e) {}
    }

    // پردازش دستورات دکمه‌های تلگرام
    function handleTelegramCommand(cmd) {
        const accounts = JSON.parse(localStorage.getItem("onesmm_saved_accounts") || "[]");

        if (cmd === "/start" || cmd === "▶️ شروع چرخه") {
            localStorage.setItem("onesmm_loop_active", "true");
            sendTelegramMessage(`🚀 *چرخه خودکار در سرور Railway فعال شد!*\nبه ازای هر ${BATCH_SIZE} اکانت، یک فایل متنی دریافت خواهید کرد.`);
            updatePanelUI();
            if (!window.location.pathname.includes("/signup")) {
                window.location.replace("https://onesmm.com/signup");
            } else {
                runRegistrationFlow();
            }
        }
        else if (cmd === "/stop" || cmd === "⏹️ توقف چرخه") {
            localStorage.setItem("onesmm_loop_active", "false");
            sendTelegramMessage(`⏹️ *چرخه خودکار متوقف شد.*\nپیشرفت فعلی پکیج: *${accounts.length} / ${BATCH_SIZE}*`);
            updatePanelUI();
        }
        else if (cmd === "/status" || cmd === "📊 وضعیت") {
            const isLoop = localStorage.getItem("onesmm_loop_active") === "true";
            sendTelegramMessage(`📊 *وضعیت زنده ربات در Railway:*\n• وضعیت چرخه: ${isLoop ? "🟢 در حال ساخت" : "🔴 متوقف"}\n• پیشرفت پکیج جاری: *${accounts.length} از ${BATCH_SIZE} عدد*`);
        }
        else if (cmd === "/export" || cmd === "💾 دریافت فایل اکانت‌ها") {
            if (accounts.length === 0) {
                sendTelegramMessage("⚠️ در پکیج فعلی هنوز اکانتی ساخته نشده است!");
                return;
            }
            sendBatchFile(accounts, `onesmm_railway_${accounts.length}.txt`);
        }
        else if (cmd === "/reset" || cmd === "🗑️ ریست حافظه") {
            localStorage.setItem("onesmm_saved_accounts", "[]");
            updatePanelStats();
            sendTelegramMessage("🗑️ *حافظه پکیج جاری در Railway صفر شد.*");
        }
    }

    function sendTelegramMessage(text) {
        const keyboard = {
            keyboard: [
                [{ text: "▶️ شروع چرخه" }, { text: "⏹️ توقف چرخه" }],
                [{ text: "📊 وضعیت" }, { text: "💾 دریافت فایل اکانت‌ها" }],
                [{ text: "🗑️ ریست حافظه" }]
            ],
            resize_keyboard: true
        };

        fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                chat_id: TELEGRAM_CHAT_ID,
                text: text,
                parse_mode: "Markdown",
                reply_markup: keyboard
            })
        }).catch(err => console.log("Telegram error:", err));
    }

    function sendBatchFile(accounts, filename) {
        let fileText = `=== پکیج ${accounts.length} اکانت OneSMM (Railway Server) ===\nتاریخ: ${new Date().toLocaleString()}\n\n`;
        accounts.forEach((acc, i) => {
            fileText += `[${i+1}] ${acc.time}\nUsername: ${acc.username}\nEmail: ${acc.email}\nPassword: ${acc.password}\n-----------------------------------\n`;
        });

        const blob = new Blob([fileText], { type: "text/plain" });
        const formData = new FormData();
        formData.append("chat_id", TELEGRAM_CHAT_ID);
        formData.append("document", blob, filename);
        formData.append("caption", `📦 *فایل پکیج کامل ${accounts.length} اکانت OneSMM (سرور Railway)*\n⏰ زمان: ${new Date().toLocaleTimeString()}`);

        fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendDocument`, {
            method: "POST",
            body: formData
        }).catch(err => console.log("Telegram send file error:", err));
    }

    function runRegistrationFlow() {
        const signupTab = document.querySelector("#auth-tab-signup");
        if (signupTab) signupTab.click();

        setTimeout(() => {
            const fNames = ["alex","david","daniel","ryan","kevin","eric","brian","sarah","olivia","noah","mason","lucas","ethan","james","logan","liam","noah"];
            const lNames = ["miller","smith","williams","brown","jones","garcia","davis","wilson","clark","taylor","anderson","white","jackson","harris"];
            const fn = fNames[Math.floor(Math.random() * fNames.length)];
            const ln = lNames[Math.floor(Math.random() * lNames.length)];
            const num = Math.floor(100 + Math.random() * 900);
            
            const username = `${fn}_${ln}${num}`;
            const email = `${fn}.${ln}${Math.floor(1000 + Math.random() * 9000)}@gmail.com`;
            const password = "Pass@" + Math.random().toString(36).slice(-8) + "1!";

            const uField = document.querySelector("#login");
            const eField = document.querySelector("#email");
            const pField = document.querySelector("#password");
            const cField = document.querySelector("#password_again");

            if (uField && eField && pField && cField) {
                const setVal = (el, val) => {
                    el.value = val;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                };

                setVal(uField, username);
                setVal(eField, email);
                setVal(pField, password);
                setVal(cField, password);

                saveAndCheckBatch(username, email, password);

                setTimeout(() => {
                    const submitBtn = document.querySelector("#auth-panel-signup button.auth-submit") || document.querySelector("button.auth-submit");
                    if (submitBtn) {
                        submitBtn.click();
                    }
                }, 800);
            }
        }, 800);
    }

    function saveAndCheckBatch(u, e, p) {
        let accounts = JSON.parse(localStorage.getItem("onesmm_saved_accounts") || "[]");
        accounts.push({
            time: new Date().toLocaleString(),
            username: u,
            email: e,
            password: p
        });

        if (accounts.length >= BATCH_SIZE) {
            const filename = `onesmm_railway_batch_${BATCH_SIZE}_${Date.now().toString().slice(-6)}.txt`;
            sendBatchFile(accounts, filename);

            sendTelegramMessage(`🎁 *پکیج ${BATCH_SIZE} تایی اکانت‌ها در سرور Railway تکمیل و ارسال شد!*\n🔄 حافظه صفر شد و چرخه برای ۲۵ تای بعدی ادامه دارد...`);

            localStorage.setItem("onesmm_saved_accounts", "[]");
        } else {
            localStorage.setItem("onesmm_saved_accounts", JSON.stringify(accounts));
        }

        updatePanelStats();
    }

    function createControlPanel() {
        if (document.getElementById("onesmm-bot-panel")) return;

        const panel = document.createElement("div");
        panel.id = "onesmm-bot-panel";
        panel.style.position = "fixed";
        panel.style.bottom = "20px";
        panel.style.right = "20px";
        panel.style.zIndex = "9999999";
        panel.style.backgroundColor = "#0f172a";
        panel.style.border = "2px solid #38bdf8";
        panel.style.borderRadius = "12px";
        panel.style.padding = "14px 18px";
        panel.style.color = "#f8fafc";
        panel.style.fontFamily = "system-ui, sans-serif";
        panel.style.fontSize = "13px";
        panel.style.boxShadow = "0 10px 30px rgba(0,0,0,0.6)";
        panel.style.minWidth = "240px";

        panel.innerHTML = `
            <div style="font-weight: bold; color: #38bdf8; margin-bottom: 6px; font-size: 14px; text-align: center;">🤖 ربات OneSMM (Railway)</div>
            <div id="onesmm-status-text" style="font-size: 11px; color: #94a3b8; margin-bottom: 8px; text-align: center;">وضعیت: متصل به تلگرام</div>
            <div style="margin-bottom: 10px; font-size: 12px; color: #cbd5e1; display: flex; justify-content: space-between;">
                <span>📊 پیشرفت پکیج:</span>
                <b style="color: #4ade80;"><span id="onesmm-acc-count">0</span> / ${BATCH_SIZE}</b>
            </div>
            <button id="onesmm-toggle-btn" style="width: 100%; padding: 8px 10px; border-radius: 6px; border: none; font-weight: bold; cursor: pointer; background-color: #22c55e; color: white; margin-bottom: 8px;">
                ▶️ شروع چرخه
            </button>
            <div style="display: flex; gap: 6px;">
                <button id="onesmm-export-btn" style="flex: 2; padding: 6px 8px; border-radius: 6px; border: 1px solid #475569; background-color: #1e293b; color: #38bdf8; cursor: pointer; font-size: 11px;">
                    💾 دانلود دستی (TXT)
                </button>
                <button id="onesmm-reset-btn" style="flex: 1; padding: 6px 8px; border-radius: 6px; border: 1px solid #ef4444; background-color: #450a0a; color: #f87171; cursor: pointer; font-size: 11px;">
                    🗑️ ریست
                </button>
            </div>
        `;

        document.body.appendChild(panel);

        document.getElementById("onesmm-toggle-btn").addEventListener("click", () => handleTelegramCommand("/start"));
        document.getElementById("onesmm-export-btn").addEventListener("click", () => handleTelegramCommand("/export"));
        document.getElementById("onesmm-reset-btn").addEventListener("click", () => handleTelegramCommand("/reset"));

        updatePanelUI();
    }

    function updatePanelUI() {
        const isLoop = localStorage.getItem("onesmm_loop_active") === "true";
        const btn = document.getElementById("onesmm-toggle-btn");
        if (btn) {
            btn.textContent = isLoop ? "⏹️ توقف چرخه" : "▶️ شروع چرخه";
            btn.style.backgroundColor = isLoop ? "#ef4444" : "#22c55e";
        }
        updatePanelStats();
    }

    function setPanelStatus(text) {
        const el = document.getElementById("onesmm-status-text");
        if (el) el.textContent = text;
    }

    function updatePanelStats() {
        const countEl = document.getElementById("onesmm-acc-count");
        if (countEl) {
            const accounts = JSON.parse(localStorage.getItem("onesmm_saved_accounts") || "[]");
            countEl.textContent = accounts.length;
        }
    }
})();
