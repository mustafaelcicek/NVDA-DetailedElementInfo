// Comprehensive JS-level regression tests for Detailed Element Info Chrome Bridge
// Loads and executes ACTUAL production Bridge/content.js and Bridge/background.js.
// No duplicated algorithms or fake copies.

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const contentJsSource = fs.readFileSync(path.join(__dirname, "../Bridge/content.js"), "utf8");
const backgroundJsSource = fs.readFileSync(path.join(__dirname, "../Bridge/background.js"), "utf8");

function createMockElement(opts = {}) {
    return {
        tagName: (opts.tagName || "DIV").toUpperCase(),
        id: opts.id || "",
        className: opts.className || "",
        type: opts.type || "",
        autocomplete: opts.autocomplete || "",
        isConnected: opts.isConnected !== false,
        attrs: Object.assign({}, opts.attrs || {}),
        getAttribute(k) {
            if (k === "id") return this.id || null;
            if (k === "class") return this.className || null;
            if (k === "type") return this.type || null;
            return this.attrs[k] || null;
        },
        setAttribute(k, v) { this.attrs[k] = String(v); },
        removeAttribute(k) { delete this.attrs[k]; },
        getBoundingClientRect() {
            return { width: 100, height: 30, top: 0, left: 0, right: 100, bottom: 30 };
        },
        cloneNode(_deep) {
            return createMockElement(opts);
        },
        querySelectorAll(_sel) { return []; }
    };
}

function loadContentScript(initialUrl = "https://example.com/app", domNodes = []) {
    const docNodes = domNodes.slice();
    const mockDoc = {
        location: { href: initialUrl },
        getElementById(id) {
            return docNodes.find(n => n.id === id) || null;
        },
        querySelectorAll(selector) {
            if (selector.startsWith('[id="') && selector.endsWith('"]')) {
                const targetId = selector.slice(5, -2);
                return docNodes.filter(n => n.id === targetId);
            }
            if (selector === "button") {
                return docNodes.filter(n => n.tagName.toLowerCase() === "button");
            }
            return [];
        }
    };

    const windowEvents = {};
    const mockWindow = {
        location: { href: initialUrl },
        devicePixelRatio: 1,
        addEventListener: (name, listener) => { windowEvents[name] = listener; },
        removeEventListener: () => {},
    };
    mockWindow.top = mockWindow;

    const observed = {messages: [], listener: null, windowEvents};
    const mockChrome = {
        runtime: {
            sendMessage: msg => { observed.messages.push(msg); },
            onMessage: {
                addListener: fn => { observed.listener = fn; }
            }
        }
    };

    class MockElement {}
    class MockHTMLInputElement extends MockElement {}

    const sandbox = {
        window: mockWindow,
        document: mockDoc,
        chrome: mockChrome,
        Element: MockElement,
        HTMLInputElement: MockHTMLInputElement,
        CSS: {
            escape: (s) => String(s).replace(/"/g, '\\"')
        },
        URL: global.URL,
        Math: global.Math,
        String: global.String,
        setInterval: () => {},
        clearInterval: () => {},
        console: global.console,
        performance: {timeOrigin: 1000},
        observed,
    };

    vm.createContext(sandbox);
    vm.runInContext(contentJsSource, sandbox);
    return sandbox;
}

// ========================================================
// Test 1: Exact URL contract in content.js and background.js
// ========================================================
console.log("Test 1: Exact URL contract in production content.js...");
{
    const ctx = loadContentScript();
    const urlsMatch = ctx.urlsMatch;
    assert.strictEqual(typeof urlsMatch, "function", "urlsMatch must be exposed in content.js");

    // Trailing slashes must NOT match
    assert.strictEqual(
        urlsMatch("https://example.com/dir", "https://example.com/dir/"),
        false,
        "/dir and /dir/ must not be silently equated"
    );

    // Query strings must NOT match
    assert.strictEqual(
        urlsMatch("https://example.com/page?id=A", "https://example.com/page?id=B"),
        false,
        "?id=A and ?id=B must not match"
    );

    // Identical URLs must match
    assert.strictEqual(
        urlsMatch("https://example.com/dir?id=A", "https://example.com/dir?id=A"),
        true
    );

    // Different origins must NOT match
    assert.strictEqual(
        urlsMatch("https://example.com/page", "https://attacker.com/page"),
        false
    );

    // Missing or invalid URLs
    assert.strictEqual(urlsMatch(null, "https://example.com"), false);
    assert.strictEqual(urlsMatch("https://example.com", ""), false);
    assert.strictEqual(urlsMatch("not-a-url", "not-a-url-either"), false);
}

// ========================================================
// Test 2: locateElement strict matching in production content.js
// ========================================================
console.log("Test 2: locateElement strict matching in production content.js...");
{
    const btn1 = createMockElement({ tagName: "button", id: "other-btn", attrs: { role: "button" } });
    const ctx = loadContentScript("https://example.com/app", [btn1]);
    const locateElement = ctx.locateElement;
    assert.strictEqual(typeof locateElement, "function", "locateElement must be exposed in content.js");

    // A generic selector 'button' when targeting 'Missing target' must NOT match unrelated button
    const missingTargetResult = locateElement(
        { tag: "button", name: "Missing target", nvda_selector: "button" },
        "https://example.com/app"
    );
    assert.strictEqual(
        missingTargetResult.element,
        null,
        "Generic selector 'button' must NOT match an unrelated button when no reliable identity exists"
    );
    assert.ok(
        missingTargetResult.error,
        "Must return an explicit error explaining absence of reliable unique identity"
    );
}

// ========================================================
// Test 3: Duplicate ID rejection in production content.js
// ========================================================
console.log("Test 3: Duplicate ID rejection in production content.js...");
{
    const dup1 = createMockElement({ tagName: "div", id: "dup-id" });
    const dup2 = createMockElement({ tagName: "div", id: "dup-id" });
    const ctx = loadContentScript("https://example.com/app", [dup1, dup2]);
    const locateElement = ctx.locateElement;

    // locateElement with id 'dup-id' must reject duplicate IDs
    const res = locateElement({ id: "dup-id", tag: "div" }, "https://example.com/app");
    assert.strictEqual(res.element, null, "Must not match when duplicate IDs exist on document");
    assert.ok(res.error && res.error.includes("Duplicate ID"), "Error must state duplicate ID");
}

// ========================================================
// Test 4: Unique ID matching in production content.js
// ========================================================
console.log("Test 4: Unique ID matching in production content.js...");
{
    const uniqueBtn = createMockElement({ tagName: "button", id: "submit-btn" });
    const ctx = loadContentScript("https://example.com/app", [uniqueBtn]);
    const locateElement = ctx.locateElement;

    const res = locateElement({ id: "submit-btn", tag: "button" }, "https://example.com/app");
    assert.strictEqual(res.element, uniqueBtn, "Must match unique stable ID");
    assert.strictEqual(res.element.isConnected, true);
}

// ========================================================
// Test 5: Disconnected element rejection in production content.js
// ========================================================
console.log("Test 5: Disconnected element rejection in production content.js...");
{
    const detached = createMockElement({ tagName: "button", id: "detached-btn", isConnected: false });
    const ctx = loadContentScript("https://example.com/app", [detached]);
    const locateElement = ctx.locateElement;

    const res = locateElement({ id: "detached-btn", tag: "button" }, "https://example.com/app");
    assert.strictEqual(res.element, null, "Disconnected element must be rejected");
}


{
    const ctx = loadContentScript("https://example.test/page");
    const nonce = ctx.observed.messages[0].documentNonce;
    ctx.observed.listener({action: "prepare_element", request_id: "probe",
                           documentNonce: nonce, deadline_ms: Date.now() + 1000}, {}, () => {});
    assert.strictEqual(ctx.observed.messages.filter(m => m.action === "bridge_ready").length, 0);
    ctx.observed.listener({action: "prepare_element", request_id: "probe",
                           documentNonce: nonce, expected_url: "https://example.test/page",
                           deadline_ms: Date.now() + 1000}, {}, () => {});
    assert.strictEqual(ctx.observed.messages.filter(m => m.action === "bridge_ready").length, 1);
    const cleaned = ctx.sanitizeFrameworkEvents({
        "__reactProps$probe": {onClick: "function", onInput: {nested: "X".repeat(100000)}},
        "unknown": {onClick: "function"},
    });
    assert.strictEqual(JSON.stringify(cleaned), '{"react":{"onClick":"function"}}');
    ctx.observed.windowEvents.pagehide({});
    assert.ok(ctx.observed.messages.some(m => m.action === "page_inactive"));
    const readyCount = ctx.observed.messages.filter(m => m.action === "bridge_ready").length;
    ctx.observed.listener({action: "prepare_element", request_id: "hidden",
                           documentNonce: nonce, expected_url: "https://example.test/page",
                           deadline_ms: Date.now() + 1000}, {}, () => {});
    assert.strictEqual(ctx.observed.messages.filter(m => m.action === "bridge_ready").length, readyCount);
    ctx.observed.windowEvents.pageshow({persisted: true});
    const newNonce = ctx.observed.messages.filter(m => m.action === "ping").slice(-1)[0].documentNonce;
    assert.notStrictEqual(newNonce, nonce);
    ctx.observed.listener({action: "prepare_element", request_id: "old-epoch",
                           documentNonce: nonce, expected_url: "https://example.test/page",
                           deadline_ms: Date.now() + 1000}, {}, () => {});
    assert.strictEqual(ctx.observed.messages.filter(m => m.action === "bridge_ready").length, readyCount);
}

async function backgroundHarness({holdUpdate = false} = {}) {
    let listener;
    let releasePoll;
    let polls = 0;
    const posts = [];
    const sent = [];
    const events = {};
    const event = name => ({addListener: fn => { events[name] = fn; }});
    const chrome = {
        runtime: {lastError: null, onMessage: {addListener: fn => { listener = fn; }}},
        tabs: {
            query: (_query, cb) => cb([{id: 3}]),
            sendMessage: (id, message, options, cb) => {
                sent.push({id, message, options});
                if (cb) cb();
            },
            onUpdated: event("updated"), onRemoved: event("removed"),
            onReplaced: event("replaced"), onActivated: event("activated"),
        },
    };
    const fetch = (url, options = {}) => {
        if (url.endsWith("/poll")) {
            polls++;
            return polls === 1 ? new Promise(resolve => { releasePoll = resolve; }) : new Promise(() => {});
        }
        const body = JSON.parse(options.body);
        posts.push({url, body, signal: options.signal});
        if (holdUpdate && body.result) return new Promise(() => {});
        return Promise.resolve({ok: true, status: 200});
    };
    const ctx = {chrome, fetch, URL, AbortController, console,
                 setTimeout: () => 1, clearTimeout: () => {}};
    vm.createContext(ctx);
    vm.runInContext(backgroundJsSource, ctx);
    const sender = {tab: {id: 3, active: true}, frameId: 0, documentId: "document-A",
                    documentLifecycle: "active", url: "https://example.test/page"};
    listener({action: "ping", documentNonce: "nonce-A", timeOrigin: 1000}, sender, () => {});
    const request = {action: "get_dom", request_id: "probe",
                     expected_url: sender.url, target: {tag: "button", id: "probe"},
                     captured_at_ms: Date.now() + 1, deadline_ms: Date.now() + 1900};
    releasePoll({ok: true, json: async () => request});
    const flush = async () => { for (let n = 0; n < 20; n++) await Promise.resolve(); };
    await flush();
    return {listener, sender, posts, sent, events, flush, request};
}

(async () => {
    const beforeBind = await backgroundHarness();
    beforeBind.listener({action: "dom_result", request_id: "probe", documentNonce: "nonce-A",
                         connected_target: true, result: {tag: "button"}},
                        beforeBind.sender, () => {});
    await beforeBind.flush();
    assert.strictEqual(beforeBind.posts.filter(p => p.body.result).length, 0,
                       "Actual background must not accept a DOM result before binding");

    const h = await backgroundHarness();
    h.listener({action: "bridge_ready", request_id: "probe",
                documentNonce: "nonce-A", timeOrigin: 1000}, h.sender, () => {});
    await h.flush();
    assert.ok(h.posts.some(p => p.url.endsWith("/bind")), "Ready must bind the request on the server");
    const collect = h.sent.find(p => p.message.action === "collect_element");
    assert.ok(collect, "Collection must start only after bind succeeds");
    assert.strictEqual(collect.options.documentId, "document-A");
    h.listener({action: "dom_result", request_id: "probe", documentNonce: "nonce-A",
                timeOrigin: 1000, connected_target: true, result: {tag: "button"}},
               {...h.sender, documentId: "document-B"}, () => {});
    await h.flush();
    assert.strictEqual(h.posts.filter(p => p.body.result).length, 0,
                       "Different document cannot complete the pinned request");
    const pending = await backgroundHarness({holdUpdate: true});
    pending.listener({action: "bridge_ready", request_id: "probe",
                      documentNonce: "nonce-A", timeOrigin: 1000}, pending.sender, () => {});
    await pending.flush();
    pending.listener({action: "dom_result", request_id: "probe", documentNonce: "nonce-A",
                      timeOrigin: 1000, connected_target: true, result: {tag: "button"}},
                     pending.sender, () => {});
    await pending.flush();
    const delivery = pending.posts.find(p => p.body.result);
    assert.ok(delivery);
    pending.events.updated(3, {status: "loading"});
    assert.strictEqual(delivery.signal.aborted, true,
                       "Navigation must abort a final delivery awaiting acknowledgment");
    console.log("Actual background handshake, changed-document and handoff-cancellation checks passed.");
})().catch(error => { console.error(error); process.exitCode = 1; });
