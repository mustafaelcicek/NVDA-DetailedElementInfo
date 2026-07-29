window.addEventListener("NVDA_EXTRACT_FRAMEWORK_EVENTS", event => {
    const targetId = event.detail;
    const targetElement = document.querySelector(`[data-nvda-target-id="${targetId}"]`);
    const frameworkProps = {};

    if (targetElement) {
        try {
            for (const key of Object.keys(targetElement)) {
                if (
                    key.startsWith("__reactProps")
                    || key.startsWith("__reactEventHandlers")
                    || key.startsWith("__vue__")
                ) {
                    const handlers = {};

                    for (const property of Object.keys(targetElement[key])) {
                        if (typeof targetElement[key][property] === "function") {
                            handlers[property] = "function";
                        } else if (property === "children") {
                            handlers[property] = "contains framework children";
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
