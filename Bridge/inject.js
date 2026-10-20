window.addEventListener("NVDA_EXTRACT_FRAMEWORK_EVENTS", event => {
    const targetId = event.detail;
    if (!targetId || typeof targetId !== "string" || targetId.length > 100 || !/^[a-zA-Z0-9_-]+$/.test(targetId)) {
        return;
    }

    let targetElement = null;
    try {
        targetElement = document.querySelector(`[data-nvda-target-id="${targetId}"]`);
    } catch (_e) {
        return;
    }

    const frameworkProps = {};

    if (targetElement) {
        try {
            let keyCount = 0;
            for (const key of Object.keys(targetElement)) {
                if (keyCount >= 50) {
                    break;
                }
                if (
                    key.startsWith("__reactProps")
                    || key.startsWith("__reactEventHandlers")
                    || key.startsWith("__vue__")
                ) {
                    keyCount++;
                    const handlers = {};
                    let propCount = 0;

                    const container = targetElement[key];
                    if (container && typeof container === "object") {
                        for (const property of Object.keys(container)) {
                            if (propCount >= 50) {
                                break;
                            }
                            propCount++;
                            if (typeof container[property] === "function") {
                                handlers[property] = "function";
                            } else if (property === "children") {
                                handlers[property] = "contains framework children";
                            }
                        }
                    }

                    frameworkProps[key] = handlers;
                }
            }
        } catch (_error) {
            // Framework internals are optional and may reject property access.
        }
    }

    window.postMessage(
        {
            type: "DOM_EVENTS_EXTRACTED",
            id: targetId,
            frameworkProps
        },
        "*"
    );
});
