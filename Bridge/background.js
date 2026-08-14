let retryDelay = 3000; 
const MAX_RETRY_DELAY = 60000;

function poll() {
    fetch('http://127.0.0.1:63333/poll', {
        method: 'GET',
        cache: 'no-cache'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Server responded with an error');
        }
        return response.json();
    })
    .then(data => {
        
        retryDelay = 3000;

        if (data.action === "get_dom") {
            
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                if (tabs && tabs.length > 0) {
                    let activeTab = tabs[0];
                    chrome.tabs.sendMessage(activeTab.id, {
                        action: "get_active_element", 
                        target: data.target 
                    }, function(response) {
                        let payload = response;
                        if (chrome.runtime.lastError) {
                            console.error(chrome.runtime.lastError);
                            payload = {"hata": "Eklenti bu sayfada okuma yapamıyor (sayfa yenilenmemiş veya chrome:// sayfası olabilir)."};
                        }
                        
                        
                        fetch('http://127.0.0.1:63333/update', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(payload || {})
                        }).catch(err => console.error("Update işlemi başarısız", err));
                    });
                }
            });
        }
        
        
        poll();
    })
    .catch(error => {
        console.log(`NVDA sunucusu kapalı veya hata oluştu. ${retryDelay / 1000} saniye sonra tekrar denenecek...`);
        setTimeout(poll, retryDelay);
        
        
        if (retryDelay < MAX_RETRY_DELAY) {
            retryDelay = Math.min(retryDelay * 2, MAX_RETRY_DELAY);
        }
    });
}


poll();


chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "ping") {
        sendResponse("pong");
        return true;
    }
});
