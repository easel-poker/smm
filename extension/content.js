// ─── تنظیمات افزونه OneSMM ─────────────────────────────────
const LOGOUT_WAIT_SEC = 3;
const PYTHON_API_URL  = "http://127.0.0.1:5000";
// ──────────────────────────────────────────────────────────

(function() {
    'use strict';

    console.log("🚀 OneSMM Extension injected into:", window.location.href);

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
                }, 350);
            }
        }, 250);

        setTimeout(() => clearInterval(checkCaptcha), 20000);
        return;
    }

    // ۲. چرخه ثبت‌نام OneSMM
    if (window.location.hostname.includes("onesmm.com")) {
        // ایجاد قطعی پنل
        createControlPanel();

        // پایش مداوم پنل و لاگین
        setInterval(() => {
            if (document.body && !document.getElementById("onesmm-bot-panel")) {
                createControlPanel();
            }

            if (localStorage.getItem("onesmm_loop_active") !== "false" && isUserActuallyLoggedIn() && !window.onesmm_is_logging_out) {
                window.onesmm_is_logging_out = true;
                handleLoggedInAccount();
            }
        }, 800);

        // شروع جریان کار
        setTimeout(processFlow, 600);
    }

    function processFlow() {
        const isLoopActive = localStorage.getItem("onesmm_loop_active") !== "false";
        if (!isLoopActive) return;

        const path = window.location.pathname.toLowerCase();

        // الف) اگر کاربر داخل اکانت است -> صبر ۳ ثانیه‌ای و خروج
        if (isUserActuallyLoggedIn()) {
            if (!window.onesmm_is_logging_out) {
                window.onesmm_is_logging_out = true;
                handleLoggedInAccount();
            }
            return;
        }

        window.onesmm_is_logging_out = false;

        // ب) اگر در صفحه ثبت‌نام است -> پر کردن فرم
        if (path.includes("signup") || path.includes("register") || document.querySelector("#auth-tab-signup")) {
            setPanelStatus("✍️ پر کردن اطلاعات ثبتنام...");
            setTimeout(runRegistrationFlow, 500);
            return;
        }

        // ج) اگر در صفحه دیگری است -> هدایت به signup
        setPanelStatus("🔄 هدایت به صفحه ثبتنام (signup)...");
        setTimeout(() => {
            window.location.href = "https://onesmm.com/signup";
        }, 800);
    }

    function isUserActuallyLoggedIn() {
        return document.querySelector("a[href*='/logout'], a[href*='logout'], a[href*='signout'], .user-avatar, .account-balance, a[href*='/orders'], a[href*='/dashboard']") !== null;
    }

    function handleLoggedInAccount() {
        let remaining = LOGOUT_WAIT_SEC;
        setPanelStatus(`🎉 اکانت لود شد! خروج تا ${remaining} ثانیه دیگر...`);

        const timer = setInterval(() => {
            remaining--;
            if (remaining > 0) {
                setPanelStatus(`⏳ لود اکانت فعال است. خروج تا ${remaining} ثانیه دیگر...`);
            } else {
                clearInterval(timer);
                setPanelStatus("🚪 در حال خروج از اکانت...");

                const logoutBtn = document.querySelector("a[href*='logout'], a[href*='signout']");
                if (logoutBtn) {
                    logoutBtn.click();
                } else {
                    window.location.href = "https://onesmm.com/logout";
                }
            }
        }, 1000);
    }

    function setNativeValue(el, val) {
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
    }

    function runRegistrationFlow() {
        const signupTab = document.querySelector("#auth-tab-signup") || 
                          Array.from(document.querySelectorAll("a, button, div, span")).find(el => 
                              el.innerText && el.innerText.trim() === "Sign up" && !el.classList.contains("auth-submit") && el.tagName !== "BUTTON"
                          );
        if (signupTab) {
            signupTab.click();
        }

        setTimeout(() => {
            const fNames = ["alex","david","daniel","ryan","kevin","eric","brian","sarah","olivia","noah","mason","lucas","ethan","james","logan","liam","adam","ben"];
            const lNames = ["miller","smith","williams","brown","jones","garcia","davis","wilson","clark","taylor","anderson","white","jackson","harris"];
            const fn = fNames[Math.floor(Math.random() * fNames.length)];
            const ln = lNames[Math.floor(Math.random() * lNames.length)];
            const num = Math.floor(100 + Math.random() * 900);

            const username = `${fn}_${ln}${num}`;
            const email = `${fn}.${ln}${Math.floor(1000 + Math.random() * 90000)}@gmail.com`;
            const password = "Pass@" + Math.random().toString(36).slice(-8) + "9!";

            const passInputs = document.querySelectorAll("#auth-panel-signup input[type='password'], form input[type='password'], input[type='password']");
            const uField = document.querySelector("#login") || document.querySelector("input[name='login']") || document.querySelector("input[name='username']") || document.querySelector("input[placeholder*='Username' i]");
            const eField = document.querySelector("#email") || document.querySelector("input[name='email']") || document.querySelector("input[type='email']") || document.querySelector("input[placeholder*='Email' i]");
            const pField = document.querySelector("#password") || document.querySelector("input[name='password']") || passInputs[0];
            const cField = document.querySelector("#password_again") || document.querySelector("input[name='password_again']") || document.querySelector("input[name='password_confirmation']") || document.querySelector("input[placeholder*='Confirm' i]") || passInputs[1];

            if (uField && eField && pField && cField) {
                setNativeValue(uField, username);
                setNativeValue(eField, email);
                setNativeValue(pField, password);
                setNativeValue(cField, password);

                sessionStorage.setItem("onesmm_current_candidate", JSON.stringify({
                    time: new Date().toLocaleString(),
                    username: username,
                    email: email,
                    password: password
                }));

                // ۱. کلیک اول روی Sign up تا کادر کپچا ظاهر شود
                setPanelStatus("🚀 ۱. کلیک Sign up برای احضار کپچا...");
                setTimeout(() => {
                    clickSignupButton();

                    // ۲. منتظر ماندن برای تایید کپچا
                    setPanelStatus("⏳ ۲. در انتظار تایید تیک کپچا...");
                    listenForCaptchaSuccess();
                }, 500);

            } else {
                setPanelStatus("⚠️ در حال آماده‌سازی فیلدها...");
                setTimeout(runRegistrationFlow, 800);
            }
        }, 400);
    }

    function clickSignupButton() {
        const submitBtn = document.querySelector("#auth-panel-signup button.auth-submit") ||
                          document.querySelector("#auth-panel-signup button[type='submit']") ||
                          document.querySelector("button.auth-submit") ||
                          document.querySelector("form button[type='submit']") ||
                          Array.from(document.querySelectorAll("button")).find(b => b.innerText && b.innerText.includes("Sign up"));

        if (submitBtn) {
            submitBtn.click();
        }
    }

    function listenForCaptchaSuccess() {
        let isDone = false;
        let waitSeconds = 0;

        const interval = setInterval(() => {
            if (isDone) {
                clearInterval(interval);
                return;
            }

            waitSeconds += 0.3;

            const hcaptchaResp = document.querySelector("[name='h-captcha-response'], [name='g-recaptcha-response']");
            const isSolved = hcaptchaResp && hcaptchaResp.value && hcaptchaResp.value.trim().length > 10;

            if (isSolved) {
                isDone = true;
                clearInterval(interval);
                setPanelStatus("🎯 کپچا تایید شد! در حال انتقال خودکار به اکانت...");
                saveCandidateAccount();
            } else if (waitSeconds > 35) {
                clearInterval(interval);
                setPanelStatus("⚠️ زمان انتظار کپچا تمام شد -> رفرش...");
                setTimeout(() => {
                    window.location.href = "https://onesmm.com/signup";
                }, 1500);
            }
        }, 300);
    }

    function saveCandidateAccount() {
        const candidate = sessionStorage.getItem("onesmm_current_candidate");
        if (candidate) {
            let accounts = JSON.parse(localStorage.getItem("onesmm_saved_accounts") || "[]");
            const acc = JSON.parse(candidate);

            if (!accounts.some(a => a.username === acc.username)) {
                accounts.push(acc);
                localStorage.setItem("onesmm_saved_accounts", JSON.stringify(accounts));
                updatePanelStats();

                // ارسال اکانت به سرور پایتون برای تلگرام
                fetch(PYTHON_API_URL, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(acc)
                }).catch(() => {});
            }
            sessionStorage.removeItem("onesmm_current_candidate");
        }
    }

    function createControlPanel() {
        if (document.getElementById("onesmm-bot-panel") || !document.body) return;

        const panel = document.createElement("div");
        panel.id = "onesmm-bot-panel";
        panel.style.position = "fixed";
        panel.style.bottom = "20px";
        panel.style.right = "20px";
        panel.style.zIndex = "99999999";
        panel.style.backgroundColor = "#0f172a";
        panel.style.border = "2px solid #38bdf8";
        panel.style.borderRadius = "12px";
        panel.style.padding = "14px 18px";
        panel.style.color = "#f8fafc";
        panel.style.fontFamily = "system-ui, sans-serif";
        panel.style.fontSize = "13px";
        panel.style.boxShadow = "0 10px 30px rgba(0,0,0,0.6)";
        panel.style.minWidth = "260px";

        const isLoop = localStorage.getItem("onesmm_loop_active") !== "false";

        panel.innerHTML = `
            <div style="font-weight: bold; color: #38bdf8; margin-bottom: 6px; font-size: 14px; text-align: center;">🤖 چرخه خودکار OneSMM</div>
            <div id="onesmm-status-text" style="font-size: 11px; color: #94a3b8; margin-bottom: 8px; text-align: center;">وضعیت: آماده</div>
            <div style="margin-bottom: 10px; font-size: 12px; color: #cbd5e1; display: flex; justify-content: space-between;">
                <span>📊 اکانتهای موفق:</span>
                <b id="onesmm-acc-count" style="color: #4ade80;">0</b>
            </div>
            <button id="onesmm-toggle-btn" style="width: 100%; padding: 8px 10px; border-radius: 6px; border: none; font-weight: bold; cursor: pointer; background-color: ${isLoop ? '#ef4444' : '#22c55e'}; color: white; margin-bottom: 8px;">
                ${isLoop ? '⏹️ توقف چرخه' : '▶️ شروع چرخه خودکار'}
            </button>
            <button id="onesmm-force-submit-btn" style="width: 100%; padding: 6px; border-radius: 6px; border: 1px solid #0284c7; background-color: #0369a1; color: white; cursor: pointer; font-size: 11px; margin-bottom: 8px;">
                ⚡ کلیک Sign up
            </button>
            <div style="display: flex; gap: 6px;">
                <button id="onesmm-export-btn" style="flex: 2; padding: 6px 8px; border-radius: 6px; border: 1px solid #475569; background-color: #1e293b; color: #38bdf8; cursor: pointer; font-size: 11px;">
                    💾 دانلود (TXT)
                </button>
                <button id="onesmm-reset-btn" style="flex: 1; padding: 6px 8px; border-radius: 6px; border: 1px solid #ef4444; background-color: #450a0a; color: #f87171; cursor: pointer; font-size: 11px;">
                    🗑️ ریست
                </button>
            </div>
        `;

        document.body.appendChild(panel);

        document.getElementById("onesmm-toggle-btn").addEventListener("click", function() {
            const current = localStorage.getItem("onesmm_loop_active") !== "false";
            if (current) {
                localStorage.setItem("onesmm_loop_active", "false");
                this.textContent = "▶️ شروع چرخه خودکار";
                this.style.backgroundColor = "#22c55e";
                setPanelStatus("چرخه متوقف شد.");
            } else {
                localStorage.setItem("onesmm_loop_active", "true");
                this.textContent = "⏹️ توقف چرخه";
                this.style.backgroundColor = "#ef4444";
                if (!window.location.pathname.includes("signup")) {
                    window.location.href = "https://onesmm.com/signup";
                } else {
                    processFlow();
                }
            }
        });

        document.getElementById("onesmm-force-submit-btn").addEventListener("click", function() {
            clickSignupButton();
        });

        document.getElementById("onesmm-export-btn").addEventListener("click", function() {
            const accounts = JSON.parse(localStorage.getItem("onesmm_saved_accounts") || "[]");
            if (accounts.length === 0) {
                alert("هنوز اکانتی در لیست ذخیره نشده است!");
                return;
            }
            let content = "=== لیست کامل اکانتهای ثبتشده OneSMM ===\n\n";
            accounts.forEach((acc, i) => {
                content += `[${i+1}] ${acc.time}\nUsername: ${acc.username}\nEmail: ${acc.email}\nPassword: ${acc.password}\n-----------------------------------\n`;
            });

            const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = `onesmm_accounts_${accounts.length}.txt`;
            link.click();
        });

        document.getElementById("onesmm-reset-btn").addEventListener("click", function() {
            const accounts = JSON.parse(localStorage.getItem("onesmm_saved_accounts") || "[]");
            if (accounts.length === 0) {
                alert("حافظه اکانتها از قبل خالی است!");
                return;
            }
            if (confirm(`⚠️ آیا مطمئن هستید که میخواهید تمام ${accounts.length} اکانت ذخیرهشده از حافظه پاک شوند؟`)) {
                localStorage.removeItem("onesmm_saved_accounts");
                sessionStorage.removeItem("onesmm_current_candidate");
                updatePanelStats();
                setPanelStatus("🗑️ حافظه اکانتها ریست شد.");
            }
        });

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
