let retryDelayMs = 3000;
const MAX_RETRY_DELAY_MS = 60000;
const BRIDGE_URL = "http://127.0.0.1:63333";

let activePendingRequest = null;

function urlsMatch(u1, u2) {
    if (!u1 || !u2 || typeof u1 !== "string" || typeof u2 !== "string") {
        return false;
    }
    try {
        const p1 = new URL(u1);
        const p2 = new URL(u2);
        if (p1.protocol.toLowerCase() !== p2.protocol.toLowerCase()) {
            return false;
        }
        if (p1.host.toLowerCase() !== p2.host.toLowerCase()) {
            return false;
        }
        if (p1.pathname !== p2.pathname) {
            return false;
        }
        if (p1.search !== p2.search) {
            return false;
        }
        return true;
    } catch (_e) {
        return false;
    }
}

const workerStartedAt = Date.now();
const witnesses = new Map();

function senderIdentity(sender) {
    if (!sender || !sender.tab || !Number.isInteger(sender.tab.id) || sender.tab.id < 0
        || sender.tab.active !== true || sender.frameId !== 0
        || sender.documentLifecycle !== "active"
        || typeof sender.documentId !== "string" || !sender.documentId
        || typeof sender.url !== "string" || !urlsMatch(sender.url, sender.url)) return null;
    return {actual_tab_id: sender.tab.id, actual_frame_id: 0,
            actual_document_id: sender.documentId, document_url: sender.url};
}

async function post(path, payload, timeoutMs = 1500, request = null) {
    const controller = new AbortController();
    if (request) request.postController = controller;
    const timer = setTimeout(() => controller.abort(), Math.max(1, timeoutMs));
    try {
        const response = await fetch(BRIDGE_URL + path, {
            method: "POST", headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload), signal: controller.signal,
        });
        return response.ok;
    } catch (_error) {
        return false;
    } finally {
        clearTimeout(timer);
    }
}

function sameDocument(left, right) {
    return left && right && left.actual_tab_id === right.actual_tab_id
        && left.actual_frame_id === right.actual_frame_id
        && left.actual_document_id === right.actual_document_id
        && urlsMatch(left.document_url, right.document_url)
        && left.document_instance_nonce === right.document_instance_nonce
        && left.document_time_origin_ms === right.document_time_origin_ms;
}

function fail(request, reason) {
    if (request !== activePendingRequest) return;
    activePendingRequest = null;
    if (request.postController) request.postController.abort();
    void post("/update", {request_id: request.request_id, error: reason});
}

function current(request) {
    return request === activePendingRequest && Date.now() <= request.deadline_ms
        && sameDocument(request.witness, witnesses.get(request.tab_id));
}

function clearTab(tabId) {
    witnesses.delete(tabId);
    if (activePendingRequest && activePendingRequest.tab_id === tabId) {
        fail(activePendingRequest, "document_changed");
    }
}

async function poll() {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 12000);
    try {
        const response = await fetch(BRIDGE_URL + "/poll", {
            method: "GET", cache: "no-cache", signal: controller.signal,
        });
        if (!response.ok) throw new Error("bridge_unavailable");
        const data = await response.json();
        retryDelayMs = 3000;
        if (data.action === "get_dom") {
            if (activePendingRequest) fail(activePendingRequest, "superseded");
            const request = {...data, tab_id: null, witness: null, binding: null};
            activePendingRequest = request;
            if (typeof data.request_id !== "string" || !data.request_id
                || !urlsMatch(data.expected_url, data.expected_url)
                || !Number.isFinite(data.captured_at_ms) || workerStartedAt > data.captured_at_ms
                || !Number.isFinite(data.deadline_ms) || Date.now() > data.deadline_ms) {
                fail(request, "missing_document_witness");
            } else {
                chrome.tabs.query({active: true, lastFocusedWindow: true}, tabs => {
                    if (request !== activePendingRequest) return;
                    if (!tabs || tabs.length !== 1) return fail(request, "no_active_tab");
                    request.tab_id = tabs[0].id;
                    const witness = witnesses.get(request.tab_id);
                    if (!witness || witness.witnessed_at_ms > request.captured_at_ms
                        || witness.document_time_origin_ms > request.captured_at_ms
                        || !urlsMatch(witness.document_url, request.expected_url)) {
                        return fail(request, "missing_document_witness");
                    }
                    request.witness = {...witness};
                    chrome.tabs.sendMessage(request.tab_id, {
                        action: "prepare_element", request_id: request.request_id,
                        expected_url: request.expected_url, deadline_ms: request.deadline_ms,
                        documentNonce: witness.document_instance_nonce,
                    }, {frameId: 0, documentId: witness.actual_document_id}, () => {
                        if (chrome.runtime.lastError) fail(request, "prepare_unavailable");
                    });
                });
            }
        }
        void poll();
    } catch (_error) {
        setTimeout(poll, retryDelayMs);
        retryDelayMs = Math.min(retryDelayMs * 2, MAX_RETRY_DELAY_MS);
    } finally {
        clearTimeout(timer);
    }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message || typeof message !== "object") return;
    const identity = senderIdentity(sender);
    if (message.action === "page_inactive") {
        if (sender && sender.tab && sender.frameId === 0) clearTab(sender.tab.id);
        return;
    }
    if (message.action === "ping") {
        if (!identity || typeof message.documentNonce !== "string" || !message.documentNonce
            || message.documentNonce.length > 256 || !Number.isFinite(message.timeOrigin)
            || message.timeOrigin <= 0) return;
        const candidate = {...identity, document_instance_nonce: message.documentNonce,
                           document_time_origin_ms: message.timeOrigin};
        const previous = witnesses.get(identity.actual_tab_id);
        if (!sameDocument(previous, candidate)) clearTab(identity.actual_tab_id);
        candidate.witnessed_at_ms = sameDocument(previous, candidate) ? previous.witnessed_at_ms : Date.now();
        witnesses.set(identity.actual_tab_id, candidate);
        if (witnesses.size > 32) witnesses.delete(witnesses.keys().next().value);
        sendResponse("pong");
        return;
    }

    const request = activePendingRequest;
    if (!request || message.request_id !== request.request_id) return;
    const actual = identity && {...identity, document_instance_nonce: message.documentNonce,
                                document_time_origin_ms: message.timeOrigin};
    if (!current(request) || !sameDocument(request.witness, actual)) {
        fail(request, "document_changed");
        return;
    }
    if (message.action === "bridge_ready" && !request.binding && !request.bindingPending) {
        request.bindingPending = true;
        const binding = {...actual, witnessed_at_ms: request.witness.witnessed_at_ms};
        void post("/bind", {request_id: request.request_id, ...binding},
                  request.deadline_ms - Date.now(), request).then(ok => {
            if (!ok || !current(request)) return fail(request, "binding_unavailable");
            request.binding = binding;
            chrome.tabs.sendMessage(request.tab_id, {
                action: "collect_element", request_id: request.request_id,
                expected_url: request.expected_url, target: request.target,
                documentNonce: binding.document_instance_nonce,
                deadline_ms: request.deadline_ms,
            }, {frameId: 0, documentId: binding.actual_document_id}, () => {
                if (chrome.runtime.lastError) fail(request, "collect_unavailable");
            });
        });
    } else if (message.action === "dom_result") {
        if (!request.binding) return fail(request, "unbound_result");
        if (request.handingOff) return;
        if (message.error || message.connected_target !== true || !message.result
            || typeof message.result !== "object" || Array.isArray(message.result)) {
            return fail(request, "unavailable_result");
        }
        request.handingOff = true;
        void post("/update", {
            request_id: request.request_id, ...request.binding,
            connected_target: true, result: message.result,
        }, request.deadline_ms - Date.now(), request).then(ok => {
            if (!ok) return fail(request, "delivery_unavailable");
            // Acceptance freezes this document's historical snapshot.
            if (activePendingRequest === request) activePendingRequest = null;
        });
    }
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
    if (changeInfo.status || changeInfo.url) clearTab(tabId);
});
chrome.tabs.onRemoved.addListener(tabId => clearTab(tabId));
chrome.tabs.onReplaced.addListener((added, removed) => { clearTab(added); clearTab(removed); });
chrome.tabs.onActivated.addListener(() => {
    for (const tabId of witnesses.keys()) clearTab(tabId);
});
poll();
