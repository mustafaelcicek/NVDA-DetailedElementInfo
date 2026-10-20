let DOCUMENT_INSTANCE_NONCE = "doc-" + Math.random().toString(36).slice(2);
let preparedInspection = null;
let pageActive = true;

function announceDocument() {
    if (!pageActive || document.prerendering) return;
    try {
        chrome.runtime.sendMessage({
            action: "ping", documentNonce: DOCUMENT_INSTANCE_NONCE,
            timeOrigin: performance.timeOrigin,
        }, () => { void chrome.runtime.lastError; });
    } catch (_error) {
        // A future heartbeat can reconnect to a restarted service worker.
    }
}
window.addEventListener("pagehide", () => {
    pageActive = false;
    preparedInspection = null;
    try { chrome.runtime.sendMessage({action: "page_inactive"}); } catch (_error) {}
});
window.addEventListener("pageshow", () => {
    pageActive = true;
    preparedInspection = null;
    DOCUMENT_INSTANCE_NONCE = "doc-" + Math.random().toString(36).slice(2);
    announceDocument();
});
setInterval(announceDocument, 10000);
announceDocument();

function sanitizeFrameworkEvents(raw) {
    const result = {};
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) return result;
    for (const [family, handlers] of Object.entries(raw).slice(0, 8)) {
        const name = family.startsWith("__react") ? "react"
            : family.startsWith("__vue") ? "vue" : null;
        if (!name || !handlers || typeof handlers !== "object" || Array.isArray(handlers)) continue;
        const events = result[name] || {};
        for (const [event, kind] of Object.entries(handlers).slice(0, 16)) {
            if (/^on[A-Za-z]{1,40}$/.test(event) && kind === "function") events[event] = "function";
        }
        if (Object.keys(events).length) result[name] = events;
    }
    return result;
}

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

function isSensitiveControl(element) {
    if (!element || !(element instanceof Element)) {
        return false;
    }
    const tag = (element.tagName || "").toLowerCase();
    const type = (element.getAttribute("type") || (element instanceof HTMLInputElement ? element.type : "") || "").toLowerCase();
    const autocomplete = (element.getAttribute("autocomplete") || (element instanceof HTMLInputElement ? element.autocomplete : "") || "").toLowerCase();
    const role = (element.getAttribute("role") || "").toLowerCase();

    if (
        type === "password"
        || autocomplete === "current-password"
        || autocomplete === "new-password"
        || role === "password"
    ) {
        return true;
    }
    if (element.id && /password/i.test(element.id)) {
        return true;
    }
    return false;
}


function isEditableControl(element) {
    const tag = element.tagName.toLowerCase();
    return element.isContentEditable || tag === "textarea" || tag === "select"
        || (tag === "input" && !["button", "submit", "reset", "image"].includes(element.type));
}

function renderedState(element) {
    const own = window.getComputedStyle(element);
    const ownHidden = own.visibility === "hidden" || own.visibility === "collapse";
    let hidden = false, uncertainRendering = false;
    let inert = false, ariaHidden = false, current = element, depth = 0;
    while (current && depth < 32) {
        const css = window.getComputedStyle(current);
        hidden = hidden || css.display === "none" || Number(css.opacity) === 0
            || css.contentVisibility === "hidden";
        uncertainRendering = uncertainRendering || css.contentVisibility === "auto";
        inert = inert || current.hasAttribute("inert");
        ariaHidden = ariaHidden || current.getAttribute("aria-hidden") === "true";
        current = current.parentElement;
        depth++;
    }
    return {rendered_hidden: hidden ? true : current || uncertainRendering ? null : ownHidden ? (element.children.length ? null : true) : false,
            subtree_hidden: hidden ? true : current || uncertainRendering ? null : false,
            inert_ancestor: inert ? true : current ? null : false,
            aria_hidden_ancestor: ariaHidden ? true : current ? null : false,
            partial: Boolean(current) || uncertainRendering};
}

function safeText(element) {
    if (isSensitiveControl(element) || isEditableControl(element)) return {text: null, partial: false, redacted: true};
    if (renderedState(element).subtree_hidden !== false) return {text: null, partial: false};
    let text = "", inspected = 0, partial = false;
    const stack = [element];
    while (stack.length && inspected < 128 && text.length < 501) {
        const node = stack.pop();
        if (node === null) { text += " "; continue; }
        inspected++;
        if (node.nodeType === Node.TEXT_NODE) {
            if (node.parentElement && window.getComputedStyle(node.parentElement).visibility === "visible") {
                const remaining = 501 - text.length;
                const content = node.nodeValue || "";
                partial = partial || content.length > remaining;
                text += content.slice(0, remaining);
            }
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            if (isSensitiveControl(node) || isEditableControl(node)
                || ["SCRIPT", "STYLE", "TEMPLATE"].includes(node.tagName.toUpperCase())
                || renderedState(node).subtree_hidden !== false) continue;
            const display = window.getComputedStyle(node).display;
            if (node.tagName === "BR") { text += " "; continue; }
            if (["block", "list-item", "table-cell", "table-row", "flex", "grid", "flow-root"].includes(display)) {
                text += " ";
                stack.push(null);
            }
            // Inspect only a bounded prefix of this referenced subtree.
            const children = node.childNodes;
            const count = Math.min(children.length, 128 - inspected - stack.length);
            partial = partial || count < children.length;
            for (let i = count - 1; i >= 0; i--) stack.push(children[i]);
        }
    }
    partial = partial || stack.length > 0 || text.length > 500;
    return {text: text.replace(/\s+/g, " ").trim().slice(0, 500), partial};
}

function elementIdentity(element) {
    return {tag: element.tagName.toLowerCase(), id: (element.id || "").slice(0, 160),
            role: (element.getAttribute("role") || "").slice(0, 80)};
}

class BudgetTracker {
    constructor(maxTargets = 8, maxPerExcerpt = 500, maxTotalChars = 4000) {
        this.maxTargets = Math.max(0, Math.min(8, maxTargets));
        this.maxPerExcerpt = Math.max(0, Math.min(500, maxPerExcerpt));
        this.maxTotalChars = Math.max(0, Math.min(4000, maxTotalChars));
        this.targetCount = 0;
        this.totalChars = 0;
        this.truncated = false;
        this.references = new Map();
    }

    reference(key, resolver) {
        if (this.references.has(key)) return this.references.get(key);
        if (this.targetCount >= this.maxTargets || this.totalChars >= this.maxTotalChars) {
            this.truncated = true;
            return {node: null, status: "budget_exceeded", truncated: true};
        }
        this.targetCount++;
        const resolved = resolver();
        this.references.set(key, resolved);
        return resolved;
    }

    resolveId(token, root) {
        if (!root || root !== document) return {node: null, status: "unsupported_tree_scope"};
        return this.reference("id:" + token, () => {
            const node = document.getElementById(token);
            if (!node) return {node: null, status: "not_found"};
            const matches = document.querySelectorAll('[id="' + CSS.escape(token) + '"]');
            return matches.length === 1 ? {node, status: "resolved"} : {node: null, status: "ambiguous"};
        });
    }

    addExcerpt(text, sensitive = false) {
        if (sensitive) return {text: null, truncated: false, redacted: true};
        const clean = String(text ?? "").trim();
        const cap = Math.min(this.maxPerExcerpt, Math.max(0, this.maxTotalChars - this.totalChars));
        const truncated = clean.length > cap;
        this.truncated = this.truncated || truncated;
        this.totalChars += Math.min(clean.length, cap);
        return {text: cap > 0 ? clean.slice(0, cap) : null, truncated};
    }

    excerpt(element) {
        const safe = safeText(element);
        const excerpt = this.addExcerpt(safe.text, safe.redacted);
        excerpt.truncated = excerpt.truncated || safe.partial;
        this.truncated = this.truncated || excerpt.truncated;
        return excerpt;
    }
}

function getSafeOuterHtml(element) {
    if (isSensitiveControl(element) || isEditableControl(element)) return null;
    const escape = text => String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
    const attributes = [];
    for (let i = 0; i < Math.min(element.attributes.length, 32); i++) {
        const attribute = element.attributes[i];
        if (attribute.name !== "value" && !attribute.name.startsWith("on")) {
            attributes.push(attribute.name + '="' + escape(attribute.value.slice(0, 200)) + '"');
        }
    }
    const tag = element.tagName.toLowerCase();
    return ("<" + tag + (attributes.length ? " " + attributes.join(" ") : "") + ">"
            + escape(safeText(element).text || "") + "</" + tag + ">").slice(0, 1000);
}

function referenceTokens(raw) {
    return (raw || "").slice(0, 2000).trim().split(/\s+/).filter(Boolean).slice(0, 64);
}

function referenceSummary(token, root, budget) {
    const resolved = budget.resolveId(token, root);
    if (!resolved.node) return {id: token, resolved: false, status: resolved.status,
                               truncated: Boolean(resolved.truncated), tree_scope: root === document ? "document" : "unsupported"};
    const excerpt = budget.excerpt(resolved.node);
    return {...elementIdentity(resolved.node), id: token, resolved: true, status: "resolved",
            excerpt: excerpt.text, truncated: excerpt.truncated, tree_scope: "document"};
}

function locateElement(target, expectedUrl) {
    if (expectedUrl && !urlsMatch(window.location.href, expectedUrl)) {
        return {element: null, error: "Document URL does not match expected URL."};
    }

    if (!target || typeof target !== "object") {
        return {element: null, error: "No target criteria specified."};
    }

    if (window !== window.top) {
        return {element: null, error: "Subframes are unsupported by top-frame content script."};
    }

    // 1. Stable captured ID match
    if (target.id) {
        const targetId = String(target.id).trim();
        try {
            const idMatches = document.querySelectorAll('[id="' + CSS.escape(targetId) + '"]');
            if (idMatches.length > 1) {
                return {element: null, error: "Duplicate ID found on document: " + targetId};
            }
            if (idMatches.length === 1) {
                const el = idMatches[0];
                if (target.tag && el.tagName.toLowerCase() !== String(target.tag).toLowerCase()) {
                    return {element: null, error: "Tag mismatch for ID: " + targetId};
                }
                if (!el.isConnected) {
                    return {element: null, error: "Matched element is disconnected from DOM."};
                }
                return {element: el};
            }
            return {element: null, error: "No element found with ID: " + targetId};
        } catch (_err) {
            // Continue if CSS.escape or querySelectorAll throws
        }
    }

    // 2. Specific stable selector match (reject generic selectors like "button", "div", etc.)
    const selector = (target.nvda_selector || "").trim();
    if (selector) {
        // Generic tag-only selectors without discriminators are rejected
        const isGenericTag = /^[a-zA-Z0-9_-]+$/.test(selector);
        if (!isGenericTag) {
            try {
                const exactMatches = document.querySelectorAll(selector);
                if (exactMatches.length === 1) {
                    const candidate = exactMatches[0];
                    if (target.tag && candidate.tagName.toLowerCase() !== String(target.tag).toLowerCase()) {
                        return {element: null, error: "Tag mismatch for selector: " + selector};
                    }
                    if (!candidate.isConnected) {
                        return {element: null, error: "Matched element is disconnected from DOM."};
                    }
                    return {element: candidate};
                } else if (exactMatches.length > 1) {
                    return {element: null, error: "Selector matched multiple elements: " + selector};
                }
            } catch (_error) {
                // Ignore querySelector syntax errors
            }
        }
    }

    // No reliable unique identity available
    return {element: null, error: "No reliable unique identity available for target; native only."};
}


function boundedClosest(element, selector) {
    let current = element, depth = 0;
    while (current && depth < 32) {
        if (current.matches(selector)) return {node: current, partial: false};
        current = current.parentElement;
        depth++;
    }
    return {node: null, partial: Boolean(current)};
}

function integerAttribute(element, attribute, minimum) {
    const raw = element.getAttribute(attribute);
    if (raw === null || !/^-?\d+$/.test(raw.trim())) return null;
    const number = Number(raw);
    return Number.isSafeInteger(number) && number >= minimum ? number : null;
}

// Only direct, uniform text with a bounded, resolved paint environment is supported.
function parseSrgbColor(raw) {
    if (typeof raw !== "string") return null;
    const match = raw.match(/^rgba?\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)(?:\s*,\s*(\d*(?:\.\d+)?))?\s*\)$/);
    if (!match) return null;
    const channels = match.slice(1, 4).map(Number);
    const alpha = match[4] === undefined ? 1 : Number(match[4]);
    if (!channels.every(c => Number.isFinite(c) && c >= 0 && c <= 255)
        || !Number.isFinite(alpha) || alpha < 0 || alpha > 1) return null;
    return {channels, alpha};
}

function srgbContrast(foreground, background) {
    const luminance = channels => {
        const linear = channels.map(channel => {
            const c = channel / 255;
            return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
        });
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
    };
    const f = luminance(foreground), b = luminance(background);
    return (Math.max(f, b) + 0.05) / (Math.min(f, b) + 0.05);
}

function collectTextContrast(element) {
    const result = {source: "dom", availability: "unavailable", reason: "unsupported_text_scope",
                    text_present: null, inactive: element.matches(":disabled")};
    if (isEditableControl(element)) return result;
    if (element.childElementCount || element.childNodes.length > 16) return result;
    let hasText = false;
    for (const node of element.childNodes) {
        if (node.nodeType !== Node.TEXT_NODE) continue;
        const text = node.nodeValue || "";
        if (text.length > 500) return {...result, reason: "text_scope_truncated"};
        hasText = hasText || /\S/.test(text);
    }
    // Freeze scalar styles; getComputedStyle returns a live object.
    const style = getComputedStyle(element);
    result.font_size_px = Number.parseFloat(style.fontSize);
    result.font_weight = Number(style.fontWeight);
    const foreground = parseSrgbColor(style.color);
    if (style.webkitTextFillColor && style.webkitTextFillColor !== style.color)
        return {...result, reason: "unsupported_text_fill"};
    let background = null, current = element, depth = 0;
    while (current && depth++ < 32) {
        const s = getComputedStyle(current);
        for (const pseudo of ["::before", "::after"]) {
            const content = getComputedStyle(current, pseudo).content;
            if (content && content !== "none" && content !== "normal")
                return {...result, reason: "generated_content"};
        }
        if (Number(s.opacity) !== 1 || s.filter !== "none"
            || (s.backdropFilter && s.backdropFilter !== "none")
            || s.mixBlendMode !== "normal" || s.backgroundBlendMode !== "normal"
            || s.transform !== "none" || s.textShadow !== "none" || s.boxShadow !== "none"
            || (s.maskImage && s.maskImage !== "none")
            || (s.webkitTextStrokeWidth && Number.parseFloat(s.webkitTextStrokeWidth) !== 0)
            || s.backgroundImage !== "none") {
            return {...result, reason: "unsupported_compositing"};
        }
        if (s.display === "none" || s.visibility !== "visible"
            || (s.contentVisibility && s.contentVisibility !== "visible"))
            return {...result, reason: "text_not_visibly_resolved"};
        if (!background) {
            const color = parseSrgbColor(s.backgroundColor);
            if (!color || (color.alpha !== 0 && color.alpha !== 1))
                return {...result, reason: "unsupported_background_color"};
            if (color.alpha === 1) background = color.channels;
        }
        current = current.parentElement;
    }
    if (current) return {...result, reason: "ancestor_scope_truncated"};
    if (!hasText) return {...result, text_present: false, reason: "no_direct_text"};
    result.text_present = true;
    if (!foreground || foreground.alpha !== 1)
        return {...result, reason: "unsupported_foreground_color"};
    if (!background) return {...result, reason: "unresolved_background"};
    const bounds = element.getBoundingClientRect();
    if (bounds.width <= 0 || bounds.height <= 0)
        return {...result, reason: "empty_text_bounds"};
    // Reject any overlapping non-ancestor box; no point-sampling claim of overlay absence.
    const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_ELEMENT);
    let node = walker.currentNode, examined = 0;
    while (node && examined++ < 256) {
        if (node !== element && !node.contains(element)) {
            const s = getComputedStyle(node);
            const generated = ["::before", "::after"].some(p => {
                const content = getComputedStyle(node, p).content;
                return content && content !== "none" && content !== "normal";
            });
            if (generated || s.boxShadow !== "none" || s.textShadow !== "none"
                || s.filter !== "none" || (s.backdropFilter && s.backdropFilter !== "none")
                || s.outlineStyle !== "none"
                || (s.overflowX === "visible" && node.scrollWidth > node.clientWidth)
                || (s.overflowY === "visible" && node.scrollHeight > node.clientHeight)) {
                return {...result, reason: "unresolved_external_paint"};
            }
            const rect = node.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0 && rect.left < bounds.right && rect.right > bounds.left
                && rect.top < bounds.bottom && rect.bottom > bounds.top) {
                return {...result, reason: "overlapping_content"};
            }
        }
        node = walker.nextNode();
    }
    if (node) return {...result, reason: "paint_scope_truncated"};
    return {...result, availability: "available", reason: "uniform_opaque_direct_text",
            foreground: foreground.channels, background, ratio: srgbContrast(foreground.channels, background)};
}

function collectElementData(element, budget, forceSensitive = false) {
    const isSensitive = forceSensitive || isSensitiveControl(element);
    const style = window.getComputedStyle(element);

    // Bounding rectangle & Viewport intersection
    const rect = element.getBoundingClientRect();
    const vpWidth = window.innerWidth || document.documentElement.clientWidth;
    const vpHeight = window.innerHeight || document.documentElement.clientHeight;
    const isIntersecting = (
        rect.bottom > 0
        && rect.top < vpHeight
        && rect.right > 0
        && rect.left < vpWidth
    );
    const visibleWidth = Math.max(0, Math.min(rect.right, vpWidth) - Math.max(rect.left, 0));
    const visibleHeight = Math.max(0, Math.min(rect.bottom, vpHeight) - Math.max(rect.top, 0));
    const visibleArea = visibleWidth * visibleHeight;
    const totalArea = rect.width * rect.height;
    const intersectionRatio = totalArea > 0 ? (visibleArea / totalArea) : 0;

    const visibilityState = renderedState(element);
    const renderedHidden = visibilityState.rendered_hidden;

    // Raw attributes map
    const attributes = {};
    for (let i = 0; i < Math.min(element.attributes.length, 128); i++) {
        const attr = element.attributes[i];
        if ((isSensitive || isEditableControl(element)) && attr.name.toLowerCase() === "value") {
            attributes[attr.name] = "[redacted]";
        } else {
            attributes[attr.name] = attr.value.slice(0, 2000);
        }
    }

    const inlineEvents = {};
    for (const property of ["onclick", "onkeydown", "onkeyup", "onkeypress", "onfocus", "onblur",
                            "oninput", "onchange", "onsubmit", "onpointerdown", "onmousedown", "ontouchstart"]) {
        try {
            if (typeof element[property] === "function") inlineEvents[property] = "function";
        } catch (_error) { /* Optional event properties can be unavailable. */ }
    }

    // ARIA IDREFs resolution (budgeted)
    const ariaIdrefAttrs = [
        "aria-labelledby",
        "aria-describedby",
        "aria-details",
        "aria-errormessage",
        "aria-controls",
        "aria-owns"
    ];

    const scope = element.getRootNode();
    const ariaIdrefs = {};
    for (const attrName of ariaIdrefAttrs) {
        const raw = element.getAttribute(attrName);
        if (raw === null) continue;
        const tokens = referenceTokens(raw);
        ariaIdrefs[attrName] = {
            raw: raw.slice(0, 2000), tokens,
            targets: tokens.map(token => referenceSummary(token, scope, budget)),
            truncated: raw.length > 2000 || raw.slice(0, 2001).trim().split(/\s+/).length > 64 || budget.truncated,
        };
    }

    // Native label associations are distinct from accessible-name computation.
    const candidates = [];
    let labelPartial = false;
    const labels = element.labels;
    if (labels && labels.length) {
        for (let i = 0; i < Math.min(labels.length, 8); i++) {
            const label = labels[i];
            const reserved = budget.reference(label, () => ({node: label, status: "resolved"}));
            if (!reserved.node) { labelPartial = true; break; }
            if (renderedState(label).subtree_hidden !== false) continue;
            const excerpt = budget.excerpt(label);
            candidates.push({source_element: elementIdentity(label), text: excerpt.text,
                             truncated: excerpt.truncated});
            labelPartial = labelPartial || excerpt.truncated;
        }
        labelPartial = labelPartial || labels.length > 8;
    } else if (["button", "a"].includes(element.tagName.toLowerCase())) {
        const excerpt = budget.excerpt(element);
        candidates.push({source_element: elementIdentity(element), text: excerpt.text,
                         truncated: excerpt.truncated});
        labelPartial = excerpt.truncated;
    }
    const established = candidates.length === 1 && Boolean(candidates[0].text) && !labelPartial;
    const contextVisibleLabel = {
        candidate_text: established ? candidates[0].text : null,
        source_element: established ? candidates[0].source_element : null,
        applicability_evidence: labelPartial ? "incomplete_label_evidence"
            : candidates.length > 1 ? "multiple_visible_labels"
            : established ? "visible_associated_text" : "no_established_visible_text",
        availability: established ? "available" : "unavailable",
        candidates, truncated: labelPartial,
    };

    // 2. Context: Language & Direction
    const rawDeclaredLang = element.getAttribute("lang");
    let effectiveInheritedLang = null;
    let declaringElementIdentity = null;

    let curLangEl = element;
    let depth = 0;
    while (curLangEl && depth < 32) {
        if (curLangEl.hasAttribute("lang")) {
            const l = curLangEl.getAttribute("lang");
            if (l === "") {
                effectiveInheritedLang = "";
                declaringElementIdentity = curLangEl.tagName.toLowerCase() + (curLangEl.id ? "#" + curLangEl.id : "");
                break;
            } else if (l) {
                effectiveInheritedLang = l;
                declaringElementIdentity = curLangEl.tagName.toLowerCase() + (curLangEl.id ? "#" + curLangEl.id : "");
                break;
            }
        }
        curLangEl = curLangEl.parentElement;
        depth++;
    }

    const declaredDir = element.getAttribute("dir");
    let effectiveHtmlDir = null;
    try {
        effectiveHtmlDir = element.matches(":dir(rtl)") ? "rtl" : element.matches(":dir(ltr)") ? "ltr" : null;
    } catch (_error) {
        // Older browsers leave HTML direction unknown; CSS direction stays separate.
    }

    const contextLanguage = {
        raw_declared_lang: rawDeclaredLang,
        effective_inherited_language: effectiveInheritedLang,
        declaring_element_identity: declaringElementIdentity,
        declared_dir: declaredDir,
        effective_html_direction: effectiveHtmlDir,
        computed_css_direction: style.direction || null
    };


    // Read validity flags without invoking validation or exposing echoed user text.
    let validityFlags = null, willValidate = null, validationMsg = null;
    let validationReason = "unavailable";
    if ("validity" in element) {
        try {
            const validity = element.validity;
            if (validity) {
                validityFlags = {};
                for (const key of ["valueMissing", "typeMismatch", "patternMismatch", "tooLong",
                                   "tooShort", "rangeUnderflow", "rangeOverflow", "stepMismatch",
                                   "badInput", "customError", "valid"]) validityFlags[key] = Boolean(validity[key]);
                willValidate = Boolean(element.willValidate);
                if (!isSensitive && !isEditableControl(element) && !validity.customError) {
                    validationMsg = budget.addExcerpt(element.validationMessage || "").text;
                    validationReason = "read_only_browser_message";
                } else validationReason = "omitted_editable_or_custom_message";
            }
        } catch (_error) { validationReason = "unavailable"; }
    }
    const formSearch = boundedClosest(element, "form");
    const formNode = element.form || formSearch.node;
    const formReference = formNode ? budget.reference(formNode, () => ({node: formNode, status: "resolved"})) : null;
    const owningForm = formReference?.node ? elementIdentity(formNode) : null;
    const groupSearch = boundedClosest(element.parentElement, 'fieldset,[role="group"],[role="radiogroup"]');
    const group = groupSearch.node;
    let fieldGroup = null;
    if (group) {
        const reserved = budget.reference(group, () => ({node: group, status: "resolved"}));
        if (reserved.node) {
            let name = null, source = "unavailable", partial = false;
            let names = [];
            if (group.tagName === "FIELDSET") {
                let legend = null;
                for (let i = 0; i < Math.min(group.children.length, 32); i++) {
                    if (group.children[i].tagName === "LEGEND") { legend = group.children[i]; break; }
                }
                const reference = legend ? budget.reference(legend, () => ({node: legend, status: "resolved"})) : null;
                if (reference?.node) {
                    const excerpt = budget.excerpt(legend);
                    name = excerpt.text; partial = excerpt.truncated; source = "direct_legend_excerpt";
                }
            } else if (group.hasAttribute("aria-labelledby")) {
                const summaries = referenceTokens(group.getAttribute("aria-labelledby")).map(
                    token => referenceSummary(token, scope, budget));
                partial = summaries.some(summary => !summary.resolved || summary.truncated);
                if (!partial) name = summaries.map(summary => summary.excerpt || "").join(" ");
                names = summaries.map(({excerpt, ...identity}) => identity);
                source = "aria_labelledby_excerpts";
            } else if (group.hasAttribute("aria-label")) {
                const excerpt = budget.addExcerpt(group.getAttribute("aria-label"));
                name = excerpt.text; partial = excerpt.truncated; source = "aria_label_attribute";
            }
            const instructions = referenceTokens(group.getAttribute("aria-describedby")).map(
                token => referenceSummary(token, scope, budget));
            fieldGroup = {...elementIdentity(group),
                group_type: group.tagName === "FIELDSET" ? "fieldset" : group.getAttribute("role"),
                name, name_source: source, name_references: names,
                instructions, truncated: partial || budget.truncated};
        }
    }
    const contextForm = {
        input_type: element.getAttribute("type") || (element instanceof HTMLInputElement ? element.type : null),
        required: "required" in element ? Boolean(element.required) : null,
        aria_required: element.getAttribute("aria-required"),
        readonly: "readOnly" in element ? Boolean(element.readOnly) : null,
        aria_readonly: element.getAttribute("aria-readonly"),
        disabled: element.matches(":disabled"),
        declared_disabled: element.hasAttribute("disabled"),
        aria_invalid: element.getAttribute("aria-invalid"),
        pattern: element.getAttribute("pattern"), min: element.getAttribute("min"),
        max: element.getAttribute("max"), step: element.getAttribute("step"),
        minlength: integerAttribute(element, "minlength", 0),
        maxlength: integerAttribute(element, "maxlength", 0),
        browser_defaults: {
            default_min: element.type === "range" ? "0" : null,
            default_max: element.type === "range" ? "100" : null,
            default_step: element.type === "range" ? "1" : null,
        },
        will_validate: willValidate, validity_flags: validityFlags,
        validation_message: validationMsg, validation_message_reason: validationReason,
        owning_form: owningForm, field_group: fieldGroup,
        ancestor_search_partial: formSearch.partial || groupSearch.partial,
    };


    const isTableCell = /^(td|th)$/i.test(element.tagName)
        || /^(cell|gridcell|columnheader|rowheader)$/i.test(element.getAttribute("role") || "");
    const contextTable = {
        is_table_cell: isTableCell, owning_table: null, row_index: null, column_index: null,
        row_span: null, column_span: null, row_count: null, column_count: null,
        declared_row_count: null, declared_column_count: null,
        declared_row_index: integerAttribute(element, "aria-rowindex", 1),
        declared_col_index: integerAttribute(element, "aria-colindex", 1),
        declared_row_span: integerAttribute(element, "aria-rowspan", 1),
        declared_col_span: integerAttribute(element, "aria-colspan", 1),
        sort_state: element.getAttribute("aria-sort"),
        row_headers: [], column_headers: [], unclassified_headers: [], explicit_headers_idrefs: [],
    };
    if (isTableCell) {
        const tableSearch = boundedClosest(element, 'table,[role="table"],[role="grid"],[role="treegrid"]');
        const rowSearch = boundedClosest(element.parentElement, 'tr,[role="row"]');
        const table = tableSearch.node, row = rowSearch.node;
        contextTable.ancestor_search_partial = tableSearch.partial || rowSearch.partial;
        if (table) {
            const reference = budget.reference(table, () => ({node: table, status: "resolved"}));
            if (reference.node) {
                contextTable.owning_table = elementIdentity(table);
                const rowCount = integerAttribute(table, "aria-rowcount", -1);
                const columnCount = integerAttribute(table, "aria-colcount", -1);
                contextTable.declared_row_count = rowCount;
                contextTable.declared_column_count = columnCount;
                contextTable.row_count = rowCount > 0 ? rowCount : null;
                contextTable.column_count = columnCount > 0 ? columnCount : null;
            }
        }
        if (contextTable.declared_row_index === null && row) {
            contextTable.declared_row_index = integerAttribute(row, "aria-rowindex", 1);
            contextTable.row_index_source = contextTable.declared_row_index !== null ? "parent_row_declaration" : null;
        }
        contextTable.row_index = contextTable.declared_row_index;
        contextTable.column_index = contextTable.declared_col_index;
        contextTable.declared_parent_col_index = row ? integerAttribute(row, "aria-colindex", 1) : null;
        contextTable.parent_col_index_raw = row ? row.getAttribute("aria-colindex") : null;
        if (contextTable.column_index === null && contextTable.declared_parent_col_index !== null) {
            let offset = null;
            if (element instanceof HTMLTableCellElement && element.cellIndex < 32 && row instanceof HTMLTableRowElement) {
                offset = 0;
                for (let i = 0; i < element.cellIndex; i++) offset += row.cells[i].colSpan;
            } else if (element.previousElementSibling === null) offset = 0;
            if (offset !== null) contextTable.column_index = contextTable.declared_parent_col_index + offset;
            contextTable.column_index_source = "parent_row_declaration";
        }
        contextTable.row_span = contextTable.declared_row_span;
        contextTable.column_span = contextTable.declared_col_span;
        if (element instanceof HTMLTableCellElement) {
            contextTable.cell_ordinal = element.cellIndex >= 0 ? element.cellIndex + 1 : null;
            contextTable.row_span = element.rowSpan;
            contextTable.column_span = element.colSpan;
            if (row instanceof HTMLTableRowElement) {
                contextTable.row_ordinal = row.rowIndex >= 0 ? row.rowIndex + 1 : null;
                if (contextTable.row_index === null) contextTable.row_index = contextTable.row_ordinal;
                // Earlier rowspans require more table context than a bounded cell inspection supplies.
                if (contextTable.column_index === null && contextTable.declared_parent_col_index === null
                    && row.rowIndex === 0 && element.cellIndex < 32) {
                    let column = 1;
                    for (let i = 0; i < element.cellIndex; i++) column += row.cells[i].colSpan;
                    contextTable.column_index = column;
                }
                if (contextTable.column_index === null) contextTable.column_index_reason = "span_context_unresolved";
            }
        }
        const tokens = referenceTokens(element.getAttribute("headers"));
        contextTable.explicit_headers_idrefs = tokens;
        for (const token of tokens) {
            const resolved = budget.resolveId(token, scope);
            if (!resolved.node) {
                contextTable.unclassified_headers.push({id: token, status: resolved.status});
                continue;
            }
            const header = resolved.node;
            const owner = boundedClosest(header, 'table,[role="table"],[role="grid"],[role="treegrid"]').node;
            const excerpt = budget.excerpt(header);
            const summary = {...elementIdentity(header), name: excerpt.text, truncated: excerpt.truncated,
                             association: "explicit_headers", declared_scope: header.getAttribute("scope")};
            const axis = header.getAttribute("scope") || header.getAttribute("role") || "";
            if (owner !== table) {
                contextTable.unclassified_headers.push({...summary, status: "different_table_scope"});
            } else if (["row", "rowgroup", "rowheader"].includes(axis)) {
                contextTable.row_headers.push(summary);
            } else if (["col", "colgroup", "columnheader"].includes(axis)) {
                contextTable.column_headers.push(summary);
            } else contextTable.unclassified_headers.push({...summary, status: "axis_unknown"});
        }
    }


    const compositeSearch = boundedClosest(element,
        '[role="combobox"],[role="listbox"],[role="tree"],[role="grid"],[role="treegrid"],[role="tablist"],[role="menu"]');
    const composite = compositeSearch.node;
    const compositeReference = composite ? budget.reference(composite, () => ({node: composite, status: "resolved"})) : null;
    const owner = compositeReference?.node;
    const activeToken = element.getAttribute("aria-activedescendant")
        || (owner ? owner.getAttribute("aria-activedescendant") : null);
    const activeTokens = referenceTokens(activeToken);
    const active = activeTokens.length === 1 ? referenceSummary(activeTokens[0], scope, budget) : null;
    const domFocus = document.activeElement;
    const selected = element.getAttribute("aria-selected");
    const contextComposite = {
        owning_composite_role: owner ? owner.getAttribute("role") : null,
        owning_composite_id: owner ? owner.id.slice(0, 160) : null,
        dom_focused_element: domFocus ? {...elementIdentity(domFocus), is_same: domFocus === element} : null,
        aria_activedescendant: activeToken,
        resolved_activedescendant: active,
        active_descendant_reason: activeTokens.length > 1 ? "invalid_token_count" : active?.status || "unavailable",
        is_selected: selected === "true" ? true : selected === "false" ? false
            : (element instanceof HTMLOptionElement ? element.selected : null),
        is_focused: domFocus === element,
        ancestor_search_partial: compositeSearch.partial,
    };

    return {
        tag: element.tagName ? element.tagName.toLowerCase() : "",
        id: element.id || "",
        className: typeof element.className === "string" ? element.className : "",
        type: element.getAttribute("type") || "",
        role: element.getAttribute("role") || "",
        tabIndex: element.tabIndex,
        isContentEditable: Boolean(element.isContentEditable),
        disabled: Boolean(element.disabled || element.hasAttribute("disabled")),
        hidden: Boolean(element.hidden || element.hasAttribute("hidden")),
        inert: Boolean(element.inert || element.hasAttribute("inert")),
        isConnected: Boolean(element.isConnected),
        innerText: isSensitive ? null : safeText(element).text,
        value: null,
        href: element.href || "",
        outerHTML: isSensitive ? null : getSafeOuterHtml(element),
        document_url: window.location.href,
        document_title: document.title || "",
        documentNonce: DOCUMENT_INSTANCE_NONCE,
        frame_id: 0,
        is_top_frame: (window === window.top),
        frame_supported: (window === window.top),
        attributes,
        aria_idrefs: ariaIdrefs,
        bounds: {
            x: rect.x,
            y: rect.y,
            width: rect.width,
            height: rect.height,
            top: rect.top,
            right: rect.right,
            bottom: rect.bottom,
            left: rect.left
        },
        viewport_intersection: {
            is_intersecting: isIntersecting,
            intersection_ratio: intersectionRatio
        },
        visibility: {
            ...visibilityState,
            rendered_hidden: renderedHidden,
            display: style.display,
            visibility: style.visibility,
            opacity: style.opacity
        },
        contrast: collectTextContrast(element),
        css: {
            display: style.display,
            visibility: style.visibility,
            cursor: style.cursor,
            pointerEvents: style.pointerEvents,
            zIndex: style.zIndex,
            position: style.position,
            color: style.color,
            backgroundColor: style.backgroundColor,
            backgroundImage: style.backgroundImage,
            fontSize: style.fontSize,
            fontWeight: style.fontWeight,
            opacity: style.opacity,
            direction: style.direction
        },
        context: {
            visible_label: contextVisibleLabel,
            language: contextLanguage,
            form: contextForm,
            table: contextTable,
            composite: contextComposite
        },
        inlineEvents,
        reference_budget: {targets_used: budget.targetCount, characters_used: budget.totalChars, truncated: budget.truncated}
    };
}


const markerOwners = new WeakMap();

function acquireMarker(element, token) {
    let state = markerOwners.get(element);
    const currentMarker = element.getAttribute("data-nvda-target-id");
    if (!state || !state.tokens.includes(currentMarker)) {
        state = {original: currentMarker, tokens: []};
        markerOwners.set(element, state);
    }
    state.tokens.push(token);
    element.setAttribute("data-nvda-target-id", token);
}

function releaseMarker(element, token) {
    const state = markerOwners.get(element);
    if (!state || !state.tokens.includes(token)) return;
    state.tokens = state.tokens.filter(owner => owner !== token);
    if (element.getAttribute("data-nvda-target-id") === token) {
        const next = state.tokens.length ? state.tokens[state.tokens.length - 1] : state.original;
        if (next === null) element.removeAttribute("data-nvda-target-id");
        else element.setAttribute("data-nvda-target-id", next);
    }
    if (!state.tokens.length) markerOwners.delete(element);
}

chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
    if (!request || typeof request !== "object") return false;
    const valid = pageActive && !document.prerendering
        && typeof request.request_id === "string" && request.request_id.length > 0
        && request.request_id.length <= 128
        && request.documentNonce === DOCUMENT_INSTANCE_NONCE
        && urlsMatch(window.location.href, request.expected_url)
        && Number.isFinite(request.deadline_ms) && Date.now() <= request.deadline_ms;
    if (request.action === "prepare_element") {
        if (!valid) return false;
        preparedInspection = {request_id: request.request_id, deadline_ms: request.deadline_ms,
                              expected_url: request.expected_url, nonce: DOCUMENT_INSTANCE_NONCE};
        chrome.runtime.sendMessage({
            action: "bridge_ready", request_id: request.request_id,
            documentNonce: DOCUMENT_INSTANCE_NONCE, timeOrigin: performance.timeOrigin,
        });
        sendResponse({prepared: true});
        return false;
    }
    if (request.action !== "collect_element" || !valid || !preparedInspection
        || preparedInspection.request_id !== request.request_id
        || preparedInspection.deadline_ms !== request.deadline_ms) return false;
    const prepared = preparedInspection;
    const nonceBefore = DOCUMENT_INSTANCE_NONCE;
    const matchResult = locateElement(request.target, request.expected_url);

    if (!matchResult.element) {
        const errPayload = {
            request_id: request.request_id,
            error: matchResult.error || "No matching element was found in the page DOM."
        };
        try {
            chrome.runtime.sendMessage({
                action: "dom_result",
                request_id: request.request_id,
                documentNonce: DOCUMENT_INSTANCE_NONCE,
                timeOrigin: performance.timeOrigin,
                connected_target: false,
                result: null,
                error: errPayload.error
            });
        } catch (_e) {}
        sendResponse(errPayload);
        return false;
    }

    const element = matchResult.element;
    if (element === document.body || element === document.documentElement) {
        const errPayload = {
            request_id: request.request_id,
            error: "Inspection target resolved to root body or documentElement; element matching was not specific."
        };
        try {
            chrome.runtime.sendMessage({
                action: "dom_result",
                request_id: request.request_id,
                documentNonce: DOCUMENT_INSTANCE_NONCE,
                timeOrigin: performance.timeOrigin,
                connected_target: false,
                result: null,
                error: errPayload.error
            });
        } catch (_e) {}
        sendResponse(errPayload);
        return false;
    }

    const limits = request.target?.reference_budget || {};
    const budget = new BudgetTracker(limits.targets_remaining ?? 8, 500, limits.characters_remaining ?? 4000);
    const forceSensitive = !request.target || request.target.protection !== "unprotected";
    const elementData = collectElementData(element, budget, forceSensitive);
    if (forceSensitive) {
        elementData.attributes = {};
        elementData.context = {};
        elementData.aria_idrefs = {};
        elementData.innerText = null;
        elementData.value = null;
    }
    elementData.request_id = request.request_id;

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

        releaseMarker(element, scriptId);

        // Verify document consistency, element connection, and exact URL persistence
        const urlConsistent = !request.expected_url || urlsMatch(window.location.href, request.expected_url);
        if (!pageActive || preparedInspection !== prepared || Date.now() > prepared.deadline_ms
            || DOCUMENT_INSTANCE_NONCE !== nonceBefore || !element.isConnected || !urlConsistent
            || locateElement(request.target, request.expected_url).element !== element) {
            const errPayload = {
                request_id: request.request_id,
                error: "Element disconnected or document/URL changed during extraction."
            };
            try {
                chrome.runtime.sendMessage({
                    action: "dom_result",
                    request_id: request.request_id,
                    documentNonce: DOCUMENT_INSTANCE_NONCE,
                    timeOrigin: performance.timeOrigin,
                    connected_target: false,
                    result: null,
                    error: errPayload.error
                });
            } catch (_e) {}
            sendResponse(errPayload);
            return;
        }

        try {
            chrome.runtime.sendMessage({
                action: "dom_result",
                request_id: request.request_id,
                documentNonce: DOCUMENT_INSTANCE_NONCE,
                timeOrigin: performance.timeOrigin,
                connected_target: Boolean(element && element.isConnected),
                result: (payload && !payload.error) ? payload : null,
                error: (payload && payload.error) ? payload.error : null
            });
        } catch (_e) {}

        sendResponse(payload);
    };

    const messageListener = event => {
        if (
            event.source === window
            && event.data
            && event.data.type === "DOM_EVENTS_EXTRACTED"
            && event.data.id === scriptId
        ) {
            elementData.frameworkEvents = forceSensitive ? {} : sanitizeFrameworkEvents(event.data.frameworkProps);
            finish(elementData);
        }
    };

    acquireMarker(element, scriptId);
    window.addEventListener("message", messageListener);
    timeoutId = setTimeout(() => finish(elementData), 350);

    try {
        window.dispatchEvent(
            new CustomEvent("NVDA_EXTRACT_FRAMEWORK_EVENTS", {detail: scriptId})
        );
    } catch (_e) {
        // Continue if custom event is rejected
    }

    return true;
});
