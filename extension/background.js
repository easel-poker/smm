chrome.runtime.onInstalled.addListener(() => {
    console.log("🚀 OneSMM Background Worker Started!");
});

// تزریق تضمینی ۱۰۰٪ اسکریپت به محض باز شدن تب onesmm.com
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url && (tab.url.includes('onesmm.com') || tab.url.includes('hcaptcha.com'))) {
        chrome.scripting.executeScript({
            target: { tabId: tabId, allFrames: true },
            files: ['content.js']
        }).catch((err) => {
            console.log("Script inject notice:", err);
        });
    }
});
