let retryDelayMs = 3000;
const MAX_RETRY_DELAY_MS = 60000;
const BRIDGE_URL = "http://127.0.0.1:63333";

function postUpdate(payload) {
    return fetch(`${BRIDGE_URL}/update`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload || {})
    }).catch(error => {
        console.error("Could not send the DOM update to NVDA.", error);
    });
}

function poll() {
    fetch(`${BRIDGE_URL}/poll`, {
        method: "GET",
        cache: "no-cache"
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Bridge server returned HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        retryDelayMs = 3000;

        if (data.action === "get_dom") {
            chrome.tabs.query({active: true, currentWindow: true}, tabs => {
                if (!tabs || tabs.length === 0) {
                    postUpdate({error: "No active Chrome tab was found."});
                    return;
                }

                chrome.tabs.sendMessage(
                    tabs[0].id,
                    {
                        action: "get_active_element",
                        target: data.target
                    },
                    response => {
                        let payload = response;

                        if (chrome.runtime.lastError) {
                            payload = {
                                error: (
                                    "The extension could not read this page. Reload the page and "
                                    + "try again; browser-internal pages cannot be inspected."
                                )
                            };
                        }

                        postUpdate(payload);
                    }
                );
            });
        }

        poll();
    })
    .catch(error => {
        console.debug(
            `NVDA bridge unavailable; retrying in ${retryDelayMs / 1000} seconds.`,
            error
        );
        setTimeout(poll, retryDelayMs);
        retryDelayMs = Math.min(retryDelayMs * 2, MAX_RETRY_DELAY_MS);
    });
}

poll();

chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
    if (request.action === "ping") {
        sendResponse("pong");
    }
});
