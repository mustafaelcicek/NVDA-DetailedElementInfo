# -*- coding: utf-8 -*-

#Bu kısımla da dom verisini doğru alabildikten sonra ilgilenelim.
TAG_ARIA_ROLE = {
    "button": "button",

    "h1": "heading",
    "h2": "heading",
    "h3": "heading",
    "h4": "heading",
    "h5": "heading",
    "h6": "heading",

    "nav": "navigation",
    "main": "main",
    "aside": "complementary",
    "article": "article",

    "table": "table",
    "tr": "row",
    "td": "cell",
    "thead": "rowgroup",
    "tbody": "rowgroup",
    "tfoot": "rowgroup",

    "ul": "list",
    "ol": "list",
    "li": "listitem",

    "figure": "figure",
    "dialog": "dialog",

    "textarea": "textbox",
    "summary": "button",
    "details": "group",

    "option": "option",
    "fieldset": "group",
    "progress": "progressbar",
    "meter": "meter",
    "search": "search",
    "caption": "caption",
}


INPUT_TYPE_ARIA_ROLE = {
    "button": "button",
    "submit": "button",
    "reset": "button",
    "image": "button",

    "checkbox": "checkbox",
    "radio": "radio",
    "range": "slider",
    "number": "spinbutton",

    "search": "searchbox",

    "text": "textbox",
    "email": "textbox",
    "tel": "textbox",
    "url": "textbox",
    "password": "textbox",
}


NVDA_ROLE_TO_ARIA = {
    "EDITABLETEXT": "textbox",
    "GRAPHIC": "img",
    "STATICTEXT": "none",
    "GROUPING": "group",
    "LANDMARK": "landmark",
    "TABLEROW": "row",
    "TABLECELL": "cell",
    "TABLECOLUMNHEADER": "columnheader",
    "TABLEROWHEADER": "rowheader",
    "COMBOBOX": "combobox",
    "LISTITEM": "listitem",
    "PROGRESSBAR": "progressbar",
    "DOCUMENT": "document",
    "PANE": "group",
}


STATE_TO_ARIA = [
    ("EXPANDED", "aria-expanded", "true"),
    ("COLLAPSED", "aria-expanded", "false"),
    ("HASPOPUP", "aria-haspopup", "true"),
    ("CHECKED", "aria-checked", "true"),
    ("HALFCHECKED", "aria-checked", "mixed"),
    ("SELECTED", "aria-selected", "true"),
    ("PRESSED", "aria-pressed", "true"),
    ("READONLY", "aria-readonly", "true"),
    ("REQUIRED", "aria-required", "true"),
    ("INVALID_ENTRY", "aria-invalid", "true"),
    ("BUSY", "aria-busy", "true"),
    ("MULTISELECTABLE", "aria-multiselectable", "true"),
    ("AUTOCOMPLETE", "aria-autocomplete", "list"),
]


def getNativeAriaRole(attrs, tag):
    """
    Return the likely native HTML role for a tag.

    This is intentionally more conservative than a direct tag -> role map.
    Some HTML elements only expose a landmark/role in certain contexts.
    """
    if not tag:
        return None

    tag = tag.strip().lower()

    explicitRole = attrs.get("xml-roles", "").strip().lower()

    if explicitRole in ("none", "presentation"):
        return "none"

    if tag == "a":
        return "link" if attrs.get("href") else None

    if tag == "input":
        inputType = attrs.get("type", "").strip().lower() or "text"
        return INPUT_TYPE_ARIA_ROLE.get(inputType, "textbox")

    if tag == "select":
        if _isSelectListbox(attrs):
            return "listbox"
        return "combobox"

    if tag == "section":
        return "region" if _hasAccessibleNameHint(attrs) else None

    if tag == "form":
        return "form" if _hasAccessibleNameHint(attrs) else None

    if tag == "header":
        # Header is banner only in specific document-level contexts.
        # Without full DOM context, report this conservatively.
        return "banner?"

    if tag == "footer":
        # Footer is contentinfo only in specific document-level contexts.
        return "contentinfo?"

    if tag == "th":
        scope = attrs.get("scope", "").strip().lower()

        if scope == "row":
            return "rowheader"

        if scope in ("col", "column"):
            return "columnheader"

        return "columnheader?"

    if tag == "img":
        if explicitRole in ("none", "presentation"):
            return "none"

        alt = attrs.get("alt")

        if alt == "":
            return "none"

        return "img"

    return TAG_ARIA_ROLE.get(tag)


def getHeadingLevel(tag, attrs):
    tag = (tag or "").strip().lower()

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return tag[1]

    role = attrs.get("xml-roles", "").strip().lower()

    if role == "heading":
        return attrs.get("aria-level", "").strip() or None

    return None


def _isSelectListbox(attrs):
    if "multiple" in attrs:
        return True

    size = attrs.get("size", "").strip()

    if not size:
        return False

    try:
        return int(size) > 1
    except Exception:
        return False


def _hasAccessibleNameHint(attrs):
    if attrs.get("aria-label"):
        return True

    if attrs.get("aria-labelledby"):
        return True

    if attrs.get("name-from") in ("related element", "contents", "attribute"):
        return True

    return False