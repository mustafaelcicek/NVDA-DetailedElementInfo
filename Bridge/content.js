
setInterval(() => {
    try {
        chrome.runtime.sendMessage({ action: "ping" }, () => {
            if (chrome.runtime.lastError) {
                
            }
        });
    } catch (e) {}
}, 10000);

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "get_active_element") {
        let el = null;
        
        
        if (request.target) {
            let target = request.target;
            let targetName = (target.name || "").trim().toLowerCase();
            let brutalTargetName = targetName.replace(/\s+/g, "");
            let targetTag = (target.tag || "").toLowerCase();
            let targetId = target.id || "";
            let targetClass = target.class || "";
            let targetWidth = target.width || 0;
            let targetHeight = target.height || 0;
            let roleValue = target.role_value || -1;
            let nvdaSelector = target.nvda_selector || "";
            
            let bestScore = -1;

            function findBestIn(elements) {
                let bestE = null;
                let currentBestScore = -1;

                for (let e of elements) {
                    let score = 0;
                    let tagName = e.tagName.toLowerCase();
                    
                    let eName = (e.innerText || e.getAttribute('aria-label') || e.getAttribute('title') || e.value || "").toLowerCase();
                    let brutalEName = eName.replace(/\s+/g, "");
                    
                    if (brutalTargetName && brutalEName) {
                        if (brutalEName === brutalTargetName) score += 1000;
                        else if (brutalEName.includes(brutalTargetName) || brutalTargetName.includes(brutalEName)) score += 500;
                    }

                    
                    if (targetWidth > 0 && targetHeight > 0) {
                        let rect = e.getBoundingClientRect();
                        let physicalWidth = rect.width * window.devicePixelRatio;
                        let physicalHeight = rect.height * window.devicePixelRatio;
                        
                        if (Math.abs(physicalWidth - targetWidth) <= 5 && Math.abs(physicalHeight - targetHeight) <= 5) {
                            score += 60; 
                        }
                    }

                    if (targetTag && tagName === targetTag) score += 10;
                    if (roleValue === 42 && tagName === 'a') score += 20;
                    if (roleValue === 29 && /^h[1-6]$/.test(tagName)) score += 20;
                    if (roleValue === 8 && (tagName === 'button' || e.getAttribute('role') === 'button')) score += 20;
                    if (targetId && e.id === targetId) score += 50;
                    if (targetClass && typeof e.className === 'string' && e.className.includes(targetClass)) score += 10;

                    if (score > currentBestScore && score > 0) {
                        currentBestScore = score;
                        bestE = e;
                    }
                }
                
                if (currentBestScore > bestScore) {
                    bestScore = currentBestScore;
                    el = bestE;
                }
            }

            if (nvdaSelector) {
                try {
                    let elements = document.querySelectorAll(nvdaSelector);
                    if (elements.length === 1) {
                        el = elements[0];
                        bestScore = 10000; 
                    } else if (elements.length > 1) {
                        findBestIn(elements);
                    }
                } catch (e) {
                    // Seçici geçersizse hatayı yut
                }
            }
            
            if (bestScore <= 0) {
                let elements = document.querySelectorAll(targetTag || '*');
                findBestIn(elements);
            }
            
        } else {
            el = document.activeElement;
        }

        let elementData = {};
        if (el && el !== document.body && el !== document.documentElement) {
            
            // CSS Özellikleri (Computed Style)
            let style = window.getComputedStyle(el);
            let cssProps = {
                display: style.display,
                visibility: style.visibility,
                cursor: style.cursor,
                pointerEvents: style.pointerEvents,
                zIndex: style.zIndex,
                position: style.position,
                color: style.color,
                backgroundColor: style.backgroundColor
            };

            // YOL A (Inline Events)
            let inlineEvents = {};
            for (let prop in el) {
                if (prop && prop.startsWith('on') && el[prop] !== null) {
                    inlineEvents[prop] = typeof el[prop];
                }
            }

            elementData = {
                "tag": el.tagName ? el.tagName.toLowerCase() : "",
                "id": el.id || "",
                "className": el.className || "",
                "type": el.getAttribute("type") || "",
                "role": el.getAttribute("role") || "",
                "aria-label": el.getAttribute("aria-label") || "",
                "innerText": el.innerText ? el.innerText.substring(0, 500).trim() : "",
                "value": el.value || "",
                "href": el.href || "",
                "outerHTML": el.outerHTML ? el.outerHTML.substring(0, 1000) : "",
                "css": cssProps,
                "inlineEvents": inlineEvents
            };

            // YOL B (Framework Hack - Injection)
            let scriptId = "event-hack-script-" + Math.random().toString(36).substr(2, 9);
            el.dataset.nvdaTargetId = scriptId; 
            
            const messageListener = function(event) {
                if (event.data && event.data.type === "DOM_EVENTS_EXTRACTED" && event.data.id === scriptId) {
                    window.removeEventListener("message", messageListener);
                    delete el.dataset.nvdaTargetId;
                    
                    elementData["frameworkEvents"] = event.data.frameworkProps;
                    sendResponse(elementData);
                }
            };
            
            window.addEventListener("message", messageListener);

            window.dispatchEvent(new CustomEvent("NVDA_EXTRACT_FRAMEWORK_EVENTS", { detail: scriptId }));
            
        } else {
            elementData = {
                "HATA": "Chrome DOM içinde bu ağaca (XPath) ait hiçbir element bulunamadı."
            };
            sendResponse(elementData);
        }
    }
    return true;
});
