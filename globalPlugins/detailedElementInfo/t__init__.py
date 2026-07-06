# -*- coding: utf-8 -*-
import globalPluginHandler
import addonHandler
import api
import ui
import config
import gui
import controlTypes
import textInfos
import wx
from scriptHandler import script

addonHandler.initTranslation()

_CONFIG_SECTION = "detailedElementInfo"
_CONFIG_SPEC = {
    "showTagSummary": "boolean(default=True)",
    "showAccessibleName": "boolean(default=True)",
    "showNameSource": "boolean(default=True)",
    "showNameSourceConfidence": "boolean(default=True)",
    "showDomTag": "boolean(default=True)",
    "showDomPath": "boolean(default=True)",
    "showComputedRole": "boolean(default=True)",
    "showSemanticSource": "boolean(default=True)",
    "showNativeSemanticMismatch": "boolean(default=True)",
    "showRawAttributes": "boolean(default=True)",
    "showMsaaRole": "boolean(default=True)",
    "showAncestors": "boolean(default=True)",
}

_FIELD_OPTIONS = [
    ("showTagSummary", "{} tag has {} attributes"),
    ("showAccessibleName", "Accessible name"),
    ("showNameSource", "Name source"),
    ("showNameSourceConfidence", "Name source confidence"),
    ("showDomTag", "DOM tag"),
    ("showDomPath", "DOM path"),
    ("showComputedRole", "Computed role"),
    ("showSemanticSource", "Semantic source"),
    ("showNativeSemanticMismatch", "Native semantic mismatch"),
    ("showRawAttributes", "{} tag raw attributes:"),
    ("showMsaaRole", "MSAA Role"),
    ("showAncestors", "Parent elements"),
]


def _ensureConfigSpec():
    config.conf.spec[_CONFIG_SECTION] = _CONFIG_SPEC


class DetailedElementInfoSettingsPanel(gui.settingsDialogs.SettingsPanel):
    title = _("Detailed Element Info")

    def makeSettings(self, settingsSizer):
        helper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
        fieldsGroup = wx.StaticBoxSizer(
            wx.StaticBox(self, label=_("Choose which fields to show when element details are displayed.")),
            wx.VERTICAL
        )
        fieldsHelper = gui.guiHelper.BoxSizerHelper(self, sizer=fieldsGroup)
        self._fieldCheckBoxes = {}
        for key, label in _FIELD_OPTIONS:
            chk = wx.CheckBox(self, label=label)
            self._fieldCheckBoxes[key] = chk
            fieldsHelper.addItem(chk)
        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.selectAllBtn = wx.Button(self, label=_("Select all"))
        self.clearAllBtn = wx.Button(self, label=_("Clear all"))
        buttonsSizer.Add(self.selectAllBtn, 0, wx.RIGHT, 10)
        buttonsSizer.Add(self.clearAllBtn, 0)
        fieldsHelper.addItem(buttonsSizer)
        helper.addItem(fieldsGroup)
        self.selectAllBtn.Bind(wx.EVT_BUTTON, self._onSelectAll)
        self.clearAllBtn.Bind(wx.EVT_BUTTON, self._onClearAll)
        self._load()

    def _load(self):
        cfg = config.conf[_CONFIG_SECTION]
        for key, _label in _FIELD_OPTIONS:
            self._fieldCheckBoxes[key].SetValue(bool(cfg[key]))

    def onSave(self):
        cfg = config.conf[_CONFIG_SECTION]
        for key, _label in _FIELD_OPTIONS:
            cfg[key] = self._fieldCheckBoxes[key].GetValue()

    def _onSelectAll(self, evt):
        for key, _label in _FIELD_OPTIONS:
            self._fieldCheckBoxes[key].SetValue(True)

    def _onClearAll(self, evt):
        for key, _label in _FIELD_OPTIONS:
            self._fieldCheckBoxes[key].SetValue(False)

# HTML tag → implicit ARIA role (WAI-ARIA 1.2, simplified)
_TAG_ARIA_ROLE = {
    "a": "link",
    "button": "button",
    "h1": "heading", "h2": "heading", "h3": "heading",
    "h4": "heading", "h5": "heading", "h6": "heading",
    "nav": "navigation",
    "main": "main",
    "header": "banner",
    "footer": "contentinfo",
    "aside": "complementary",
    "article": "article",
    "section": "region",
    "form": "form",
    "table": "table",
    "tr": "row",
    "td": "cell",
    "th": "columnheader",
    "thead": "rowgroup",
    "tbody": "rowgroup",
    "tfoot": "rowgroup",
    "ul": "list",
    "ol": "list",
    "li": "listitem",
    "img": "img",
    "figure": "figure",
    "dialog": "dialog",
    "select": "combobox",
    "textarea": "textbox",
    "summary": "button",
    "details": "group",
    "menu": "list",
    "menuitem": "menuitem",
    "option": "option",
    "fieldset": "group",
    "progress": "progressbar",
    "meter": "meter",
    "search": "search",
    "output": "status",
    "caption": "caption",
}

# HTML input[type] → implicit ARIA role (common practical mapping)
_INPUT_TYPE_ARIA_ROLE = {
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

# NVDA Role enum name → ARIA role name (for fallback when tag is unknown)
_NVDA_ROLE_TO_ARIA = {
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

# NVDA State enum name → (aria attribute name, value)
# EXPANDED must be checked first to avoid conflict with COLLAPSED
_STATE_TO_ARIA = [
    ("EXPANDED",        "aria-expanded",       "true"),
    ("COLLAPSED",       "aria-expanded",       "false"),
    ("HASPOPUP",        "aria-haspopup",       "true"),
    ("CHECKED",         "aria-checked",        "true"),
    ("HALFCHECKED",     "aria-checked",        "mixed"),
    ("SELECTED",        "aria-selected",       "true"),
    ("PRESSED",         "aria-pressed",        "true"),
    ("READONLY",        "aria-readonly",       "true"),
    ("REQUIRED",        "aria-required",       "true"),
    ("INVALID_ENTRY",   "aria-invalid",        "true"),
    ("BUSY",            "aria-busy",           "true"),
    ("MULTISELECTABLE", "aria-multiselectable","true"),
    ("AUTOCOMPLETE",    "aria-autocomplete",   "list"),
]


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    scriptCategory = _("Detailed Element Info")

    def __init__(self):
        super(GlobalPlugin, self).__init__()
        _ensureConfigSpec()
        if DetailedElementInfoSettingsPanel not in gui.settingsDialogs.NVDASettingsDialog.categoryClasses:
            gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(DetailedElementInfoSettingsPanel)

    def terminate(self):
        if DetailedElementInfoSettingsPanel in gui.settingsDialogs.NVDASettingsDialog.categoryClasses:
            gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(DetailedElementInfoSettingsPanel)
        super(GlobalPlugin, self).terminate()

    @script(description=_("Show focused element details"), gesture="kb:NVDA+shift+f1", speakOnDemand=True)
    def script_showElementInfo(self, gesture):
        obj = self._getCurrentObject()
        if obj is None:
            ui.message(_("Element not found"))
            return
        
        # Check if we're on a web page
        focus = api.getFocusObject()
        if not hasattr(focus, "treeInterceptor") or focus.treeInterceptor is None:
            ui.message(_("This feature only works on web pages"))
            return
        
        ui.browseableMessage(self._buildReport(obj), title=_("Detailed Element Info"))

    def _getCurrentObject(self):
        """Returns the object focused or navigated with arrow keys."""
        focus = api.getFocusObject()
        if focus is None:
            return None
        ti = getattr(focus, "treeInterceptor", None)
        if ti is not None and not getattr(ti, "passThrough", True):
            try:
                info = ti.makeTextInfo(textInfos.POSITION_CARET)
                caretObj = info.NVDAObjectAtStart
                if caretObj is not None:
                    return caretObj
            except Exception:
                pass
        return focus

    def _buildReport(self, obj):
        cfg = config.conf[_CONFIG_SECTION]
        lines = [_("Detailed Element Info"), ""]
        lines.extend(self._fmtElem(obj, cfg))
        if cfg["showAncestors"]:
            for anc in self._ancestors(obj):
                lines.append("")
                lines.extend(self._fmtElem(anc, cfg))
        lines += ["", "", _("Press Esc to close this message")]
        return "\n".join(lines)

    def _fmtElem(self, obj, cfg):
        attrs = self._rawAttrs(obj)
        tag = attrs.get("tag", "")
        dom_path = self._buildDomPath(obj)

        name = self._getAccessibleName(obj)
        name_source, name_confidence = self._getNameSource(obj, attrs)
        computed_role = self._getComputedRole(obj, attrs, tag)
        semantic_source = self._getSemanticSource(attrs, tag)
        mismatch = self._getNativeSemanticMismatch(attrs, tag)
        msaa = self._msaaRole(obj)

        display_tag = tag.upper() if tag else "?"
        lines = []
        if cfg["showTagSummary"]:
            lines.append(_("{} tag has {} attributes").format(display_tag, len(attrs)))
        if cfg["showAccessibleName"]:
            lines.append("Accessible name: {}".format(name if name else "(none)"))
        if cfg["showNameSource"]:
            lines.append("Name source: {}".format(name_source))
        if cfg["showNameSourceConfidence"]:
            lines.append("Name source confidence: {}".format(name_confidence))
        if cfg["showDomTag"]:
            lines.append("DOM tag: {}".format(tag if tag else "unknown"))
        if cfg["showDomPath"]:
            lines.append("DOM path: {}".format(dom_path if dom_path else "unknown"))
        if cfg["showComputedRole"]:
            lines.append("Computed role: {}".format(computed_role))
        if cfg["showSemanticSource"]:
            lines.append("Semantic source: {}".format(semantic_source))
        if cfg["showNativeSemanticMismatch"]:
            lines.append("Native semantic mismatch: {}".format(mismatch))
        if cfg["showRawAttributes"] and attrs:
            lines.append("")
            lines.append(_("{} tag raw attributes:").format(display_tag))
            for k in sorted(attrs):
                lines.append("  {}={}".format(k, attrs[k]))
        if cfg["showMsaaRole"] and msaa is not None:
            lines.append("MSAA Role={:X}".format(msaa))
        if not lines:
            lines.append(_("No fields selected in settings"))

        return lines

    # ------------------------------------------------------------------ #
    #  Raw data helpers                                                    #
    # ------------------------------------------------------------------ #

    def _rawAttrs(self, obj):
        """Derived ARIA attributes from IA2Attributes + state + href."""
        d = {}
        try:
            ia2 = getattr(obj, "IA2Attributes", None)
            if ia2 is not None:
                d = dict(ia2)
        except Exception:
            pass
        # ARIA attributes derived from states (aria-expanded, aria-haspopup, etc.)
        for k, v in self._stateBasedAttrs(obj).items():
            if k not in d:
                d[k] = v
        try:
            tag = d.get("tag", "")
            if tag in ("a", "#document") and obj.value and "href" not in d:
                d["href"] = obj.value
        except Exception:
            pass
        return d

    def _stateBasedAttrs(self, obj):
        """Returns ARIA attributes derived from NVDA states."""
        result = {}
        try:
            states = obj.states
        except Exception:
            return result
        for state_name, aria_attr, aria_val in _STATE_TO_ARIA:
            state = getattr(controlTypes.State, state_name, None)
            if state is not None and state in states:
                if aria_attr not in result:   # EXPANDED/COLLAPSED conflict protection
                    result[aria_attr] = aria_val
        return result

    def _getAccessibleName(self, obj):
        """Returns NVDA's computed accessible name (obj.name)."""
        try:
            n = obj.name
            if n:
                return n
        except Exception:
            pass
        return ""

    def _getNameSource(self, obj, attrs):
        """
        Returns (source, confidence).
        Decision logic: priority order from specification.
        """
        # Certain: ARIA attributes explicitly visible in raw attrs
        if "aria-label" in attrs:
            return "aria-label", "certain"
        if "aria-labelledby" in attrs:
            return "aria-labelledby", "certain"

        name_from = attrs.get("name-from", "")

        if name_from == "value":
            return "value", "certain"
        if name_from == "contents":
            return "contents", "certain"
        if name_from == "related element":
            # aria-labelledby not in raw attrs but related element exists
            return "related element", "inferred"

        if name_from == "attribute":
            tag = attrs.get("tag", "")
            if "alt" in attrs:
                return "alt", "certain"
            if "aria-label" in attrs:       # double check (paranoia)
                return "aria-label", "certain"
            if "aria-labelledby" in attrs:
                return "aria-labelledby", "certain"
            if "title" in attrs:
                return "title", "inferred"
            if "placeholder" in attrs:
                return "placeholder", "inferred"
            if "value" in attrs:
                return "value", ("certain" if tag in ("input", "button") else "inferred")
            return "attribute", "inferred"

        # name-from missing or unknown; does accessible name exist?
        try:
            if obj.name:
                return "unknown-computed", "unknown"
        except Exception:
            pass
        return "unknown-computed", "unknown"

    def _getComputedRole(self, obj, attrs, tag):
        """
        Returns the ARIA role name.
        Priority: xml-roles (explicit ARIA) > tag native > NVDA enum name.
        """
        xml_roles = attrs.get("xml-roles", "").strip()
        if xml_roles:
            return xml_roles

        if tag:
            native = self._getNativeAriaRole(attrs, tag)
            if native:
                return native

        try:
            role = obj.role
            try:
                enum_name = controlTypes.Role(role).name
                return _NVDA_ROLE_TO_ARIA.get(enum_name, enum_name.lower())
            except Exception:
                return str(role)
        except Exception:
            return "unknown"

    def _getSemanticSource(self, attrs, tag):
        """
        native HTML | explicit role | redundant explicit role | unknown
        """
        if not tag:
            return "unknown"

        xml_roles = attrs.get("xml-roles", "").strip()
        native_aria_role = self._getNativeAriaRole(attrs, tag)

        if xml_roles:
            if native_aria_role and xml_roles.lower() == native_aria_role.lower():
                return "redundant explicit role"
            return "explicit role"
        else:
            if native_aria_role:
                return "native HTML"
            return "unknown"

    def _getNativeSemanticMismatch(self, attrs, tag):
        """
        yes | no | unknown
        """
        if not tag:
            return "unknown"

        native_aria_role = self._getNativeAriaRole(attrs, tag)
        xml_roles = attrs.get("xml-roles", "").strip()

        if native_aria_role is None:
            # Elements like div, span, p — have no native semantics
            return "yes" if xml_roles else "no"

        # Tags with native semantics: mismatch if explicit role differs
        if xml_roles and xml_roles.lower() != native_aria_role.lower():
            return "yes"
        return "no"

    def _getNativeAriaRole(self, attrs, tag):
        if not tag:
            return None
        tag = tag.lower()
        if tag != "input":
            return _TAG_ARIA_ROLE.get(tag)
        input_type = attrs.get("type", "").strip().lower()
        if not input_type:
            input_type = "text"
        return _INPUT_TYPE_ARIA_ROLE.get(input_type, "textbox")

    def _buildDomPath(self, obj, maxDepth=25):
        parts = []
        cur = obj
        depth = 0
        while cur is not None and depth < maxDepth:
            depth += 1
            attrs = self._rawAttrs(cur)
            tag = attrs.get("tag", "").strip().lower()
            if not tag:
                break
            if tag == "#document":
                break
            parts.append(self._domPathSegment(attrs))
            try:
                cur = cur.parent
            except Exception:
                break
        parts.reverse()
        return " > ".join(parts)

    def _domPathSegment(self, attrs):
        tag = attrs.get("tag", "").strip().lower()
        if not tag:
            return "unknown"
        seg = tag
        node_id = attrs.get("id", "").strip()
        if node_id:
            return "{}#{}".format(seg, node_id)
        class_attr = attrs.get("class", "").strip()
        if class_attr:
            classes = [c for c in class_attr.split() if c]
            if classes:
                return "{}{}".format(seg, "".join(".{}".format(c) for c in classes[:2]))
        name_attr = attrs.get("name", "").strip()
        if name_attr:
            return '{}[name="{}"]'.format(seg, name_attr.replace('"', '\\"'))
        role_attr = attrs.get("xml-roles", "").strip()
        if role_attr:
            return '{}[role="{}"]'.format(seg, role_attr.replace('"', '\\"'))
        return seg

    # ------------------------------------------------------------------ #
    #  Ancestor traversal                                                  #
    # ------------------------------------------------------------------ #

    def _ancestors(self, obj, maxDepth=20):
        result = []
        try:
            cur = obj.parent
        except Exception:
            return result
        count = 0
        while cur is not None and count < maxDepth:
            count += 1
            tag = None
            try:
                ia2 = getattr(cur, "IA2Attributes", None)
                if ia2:
                    tag = ia2.get("tag")
            except Exception:
                pass
            if tag is None:
                break
            result.append(cur)
            if tag == "#document":
                break
            try:
                cur = cur.parent
            except Exception:
                break
        return result

    def _msaaRole(self, obj):
        try:
            iaObj = getattr(obj, "IAccessibleObject", None)
            cid = getattr(obj, "IAccessibleChildID", 0)
            if iaObj:
                return iaObj.accRole(cid)
        except Exception:
            pass
        return None

