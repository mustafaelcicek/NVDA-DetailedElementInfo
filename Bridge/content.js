setInterval(() => {
    try {
        chrome.runtime.sendMessage({action: "ping"}, () => {
            // Reading lastError prevents Chrome from logging a noisy rejected callback.
            void chrome.runtime.lastError;
        });
    } catch (_error) {
        // The service worker will be retried by Chrome.
    }
}, 10000);

function findBestElement(elements, target) {
    const targetName = (target.name || "").trim().toLowerCase();
    const compactTargetName = targetName.replace(/\s+/g, "");
    const targetTag = (target.tag || "").toLowerCase();
    const targetId = target.id || "";
    const targetClass = target.class || "";
    const targetWidth = target.width || 0;
    const targetHeight = target.height || 0;
    const roleValue = target.role_value ?? -1;

    let bestElement = null;
    let bestScore = -1;

    for (const element of elements) {
        let score = 0;
        const tagName = element.tagName.toLowerCase();
        const elementName = (
            element.innerText
            || element.getAttribute("aria-label")
            || element.getAttribute("title")
            || element.value
            || ""
        ).toLowerCase();
        const compactElementName = elementName.replace(/\s+/g, "");

        if (compactTargetName && compactElementName) {
            if (compactElementName === compactTargetName) {
                score += 1000;
            } else if (
                compactElementName.includes(compactTargetName)
                || compactTargetName.includes(compactElementName)
            ) {
                score += 500;
            }
        }

        if (targetWidth > 0 && targetHeight > 0) {
            const rect = element.getBoundingClientRect();
            const physicalWidth = rect.width * window.devicePixelRatio;
            const physicalHeight = rect.height * window.devicePixelRatio;

            if (
                Math.abs(physicalWidth - targetWidth) <= 5
                && Math.abs(physicalHeight - targetHeight) <= 5
            ) {
                score += 60;
            }
        }

        if (targetTag && tagName === targetTag) {
            score += 10;
        }
        if (roleValue === 42 && tagName === "a") {
            score += 20;
        }
        if (roleValue === 29 && /^h[1-6]$/.test(tagName)) {
            score += 20;
        }
        if (
            roleValue === 8
            && (tagName === "button" || element.getAttribute("role") === "button")
        ) {
            score += 20;
        }
        if (targetId && element.id === targetId) {
            score += 50;
        }
        if (
            targetClass
            && typeof element.className === "string"
            && element.className.includes(targetClass)
        ) {
            score += 10;
        }

        if (score > bestScore && score > 0) {
            bestScore = score;
            bestElement = element;
        }
    }

    return {element: bestElement, score: bestScore};
}

function locateElement(target) {
    if (!target) {
        return document.activeElement;
    }

    const selector = target.nvda_selector || "";

    if (selector) {
        try {
            const exactMatches = document.querySelectorAll(selector);
            if (exactMatches.length === 1) {
                return exactMatches[0];
            }
            if (exactMatches.length > 1) {
                const exactResult = findBestElement(exactMatches, target);
                if (exactResult.element) {
                    return exactResult.element;
                }
            }
        } catch (_error) {
            // Continue with the scored fallback when a selector is not accepted.
        }
    }

    let candidates;
    try {
        candidates = document.querySelectorAll(target.tag || "*");
    } catch (_error) {
        candidates = document.querySelectorAll("*");
    }

    return findBestElement(candidates, target).element;
}

function isSensitiveControl(element) {
    if (!(element instanceof HTMLInputElement)) {
        return false;
    }

    const type = (element.type || "").toLowerCase();
    const autocomplete = (element.autocomplete || "").toLowerCase();
    return (
        type === "password"
        || autocomplete === "current-password"
        || autocomplete === "new-password"
    );
}

function getSafeOuterHtml(element) {
    const clone = element.cloneNode(true);
    const controls = [];

    if (clone instanceof HTMLInputElement) {
        controls.push(clone);
    }
    controls.push(
        ...clone.querySelectorAll(
            'input[type="password"], input[autocomplete="current-password"], '
            + 'input[autocomplete="new-password"]'
        )
    );

    for (const control of controls) {
        control.removeAttribute("value");
    }

    return (clone.outerHTML || "").substring(0, 1000);
}

function collectElementData(element) {
    const style = window.getComputedStyle(element);
    const inlineEvents = {};

    for (const property in element) {
        if (property.startsWith("on") && element[property] !== null) {
            inlineEvents[property] = typeof element[property];
        }
    }

    return {
        tag: element.tagName ? element.tagName.toLowerCase() : "",
        id: element.id || "",
        className: element.className || "",
        type: element.getAttribute("type") || "",
        role: element.getAttribute("role") || "",
        "aria-label": element.getAttribute("aria-label") || "",
        innerText: element.innerText ? element.innerText.substring(0, 500).trim() : "",
        value: isSensitiveControl(element) ? "[redacted]" : (element.value || ""),
        href: element.href || "",
        outerHTML: getSafeOuterHtml(element),
        css: {
            display: style.display,
            visibility: style.visibility,
            cursor: style.cursor,
            pointerEvents: style.pointerEvents,
            zIndex: style.zIndex,
            position: style.position,
            color: style.color,
            backgroundColor: style.backgroundColor
        },
        inlineEvents
    };
}

chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
    if (request.action !== "get_active_element") {
        return false;
    }

    const element = locateElement(request.target);

    if (!element || element === document.body || element === document.documentElement) {
        sendResponse({error: "No matching element was found in the page DOM."});
        return false;
    }

    const elementData = collectElementData(element);
    const scriptId = `nvda-target-${Math.random().toString(36).slice(2, 11)}`;
    let responded = false;
    let timeoutId;

    const finish = payload => {
        if (responded) {
            return;
        }
        responded = true;
        clearTimeout(timeoutId);
        window.removeEventListener("message", messageListener);
        delete element.dataset.nvdaTargetId;
        sendResponse(payload);
    };

    const messageListener = event => {
        if (
            event.source === window
            && event.data
            && event.data.type === "DOM_EVENTS_EXTRACTED"
            && event.data.id === scriptId
        ) {
            elementData.frameworkEvents = event.data.frameworkProps;
            finish(elementData);
        }
    };

    element.dataset.nvdaTargetId = scriptId;
    window.addEventListener("message", messageListener);
    timeoutId = setTimeout(() => finish(elementData), 750);
    window.dispatchEvent(
        new CustomEvent("NVDA_EXTRACT_FRAMEWORK_EVENTS", {detail: scriptId})
    );

    return true;
});
