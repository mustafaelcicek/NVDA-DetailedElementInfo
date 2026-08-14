window.addEventListener("NVDA_EXTRACT_FRAMEWORK_EVENTS", function(e) {
    let targetId = e.detail;
    let targetEl = document.querySelector(`[data-nvda-target-id="${targetId}"]`);
    let frameworkProps = {};
    
    if (targetEl) {
        try {
            for (let key of Object.keys(targetEl)) {
                if (key.startsWith('__reactProps') || key.startsWith('__reactEventHandlers') || key.startsWith('__vue__')) {
                    let handlers = {};
                    for (let prop of Object.keys(targetEl[key])) {
                        if (typeof targetEl[key][prop] === 'function') {
                            handlers[prop] = "function (Gizli Event)";
                        } else if (prop === 'children') {
                            handlers[prop] = "React Children İçeriyor";
                        }
                    }
                    frameworkProps[key] = handlers;
                }
            }
        } catch(err) {}
    }
    
    window.postMessage({ 
        type: "DOM_EVENTS_EXTRACTED", 
        id: targetId,
        frameworkProps: frameworkProps 
    }, "*");
});
