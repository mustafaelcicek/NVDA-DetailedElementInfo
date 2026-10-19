"""Pure HTML and Markdown views of one frozen inspection snapshot."""

import html
import json
import re
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, cast

import addonHandler
from .config import DEFAULTS

addonHandler.initTranslation()

if TYPE_CHECKING:
    # initTranslation installs the add-on translator in this module at runtime.
    def _(message: str) -> str:
        return message


Row = Tuple[str, str]
Section = Tuple[str, List[Row]]

STATUS_LABELS = {
    "pass": _("pass"),
    "fail": _("fail"),
    "warning": _("warning"),
    "unknown": _("unknown"),
    "not_applicable": _("not applicable"),
}
FINDING_MESSAGES = {
    "name_evidence_unavailable": _("Computed name or role evidence is unavailable."),
    "computed_name_present": _("The computed accessible name is present."),
    "required_computed_name_empty": _("A control requiring an accessible name has a known empty name."),
    "role_outside_name_check": _("The observed role is outside this control-name check."),
    "visible_label_evidence_unavailable": _("A visible text label or its association is not established."),
    "role_outside_label_check": _("The observed role is outside this label-in-name check."),
    "no_visible_text_label": _("No visible text label was established by applicable evidence."),
    "visible_label_in_name": _("The established visible label is included in the computed name."),
    "visible_label_missing_from_name": _("The computed name does not include the established visible label."),
    "ambiguous_symbolic_label": _("The label may contain a meaningful symbol; human review is required."),
    "image_evidence_unavailable": _("The image alternative or decorative purpose is not established."),
    "image_name_looks_like_filename": _("The image name resembles a filename; assess its purpose manually."),
    "image_computed_name_present": _("The exposed image has a computed accessible name."),
    "exposed_image_computed_name_empty": _("The exposed image has a known empty computed name."),
    "decorative_image": _("The captured evidence identifies a presentational image with empty alt."),
    "not_exposed_as_image": _("The observed role is outside this image check."),
    "event_detection_incomplete": _(
        "Event detection is incomplete; keyboard behavior has not been exercised."
    ),
    "click_requires_keyboard_review": _(
        "Click evidence needs manual review of semantics and keyboard behavior."
    ),
    "semantic_control_keyboard_not_checked": _(
        "A semantic control was observed; keyboard behavior was not tested."
    ),
    "inactive_control": _("The control is inactive."),
    "no_direct_text": _("No direct text is present in the supported scope."),
    "text_contrast_sufficient": _(
        "The resolved direct-text contrast meets the applicable numerical threshold."
    ),
    "text_contrast_below_threshold": _(
        "The resolved direct-text contrast is below the applicable threshold."
    ),
}
SCOPE_TEXT = " ".join(
    [
        _("Checks concern only the captured element and stated evidence."),
        _("Unknown means evidence is incomplete. Warnings require human judgment."),
        _("These results do not establish page-level WCAG conformance."),
    ]
)


def _value(value: Any) -> str:
    if value is None:
        return _("unavailable")
    if value == "":
        return _("empty")
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _observation(value: Any, source: str = "derived") -> str:
    if isinstance(value, dict) and "value" in value and "availability" in value and "source" in value:
        observation = cast(Dict[str, Any], value)
        parts = [
            _value(observation.get("value")),
            _("source: {}").format(observation["source"]),
            _("availability: {}").format(observation["availability"]),
        ]
        for flag in ("partial", "truncated", "protected"):
            if observation.get(flag) is True:
                parts.append(flag)
        if observation.get("reason"):
            parts.append(_("reason: {}").format(observation["reason"]))
        metadata = {
            key: item
            for key, item in observation.items()
            if key not in {"value", "source", "availability", "partial", "truncated", "protected", "reason"}
            and item is not None
        }
        if metadata:
            parts.append(_("evidence: {}").format(_value(metadata)))
        return "; ".join(parts)
    return _value(value) + "; " + _("source: {}").format(source)


def _markdown(text: str) -> str:
    text = html.escape(text, quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|>-])", r"\\\1", text).replace("\n", " ")


class ReportBuilder:
    def __init__(self, analyzer: Any = None):
        # The optional old constructor argument remains accepted; renderers never call it.
        super().__init__()

    @staticmethod
    def _snapshot(data: Any) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise TypeError("A frozen snapshot is required")
        frozen = cast(Dict[str, Any], data)
        return frozen.get("snapshot", frozen)

    def _sections(
        self,
        snapshot: Dict[str, Any],
        fields: Optional[Dict[str, Any]] = None,
        include_ancestors: bool = True,
    ) -> List[Section]:
        active_fields: Dict[str, Any] = (
            fields if fields is not None else snapshot.get("availability", {}).get("report_fields", {})
        )

        def enabled(key: str) -> bool:
            return bool(active_fields.get(key, DEFAULTS.get(key, True)))

        native = snapshot.get("native", {})
        aria = snapshot.get("aria", {})
        dom = snapshot.get("dom", {})
        context = snapshot.get("context", {})
        sections: List[Section] = []
        identity: List[Row] = []
        options: List[Tuple[str, str, Any]] = [
            ("showAccessibleName", _("Accessible name"), native.get("name")),
            ("showNameSource", _("Name source"), native.get("name_source")),
            ("showNameSourceConfidence", _("Name source confidence"), native.get("name_confidence")),
            ("showDomTag", _("DOM tag"), aria.get("tag")),
            ("showDomPath", _("DOM path"), native.get("dom_path")),
            ("showExplicitRole", _("Explicit ARIA role"), aria.get("explicit_role")),
            ("showNativeRole", _("Native HTML role"), aria.get("native_role")),
            ("showNvdaRole", _("NVDA role"), aria.get("nvda_role")),
            ("showFinalRole", _("Final inferred role"), aria.get("final_role")),
            ("showSemanticSource", _("Semantic source"), native.get("semantic_source")),
            ("showNativeSemanticMismatch", _("Native semantic mismatch"), native.get("semantic_mismatch")),
            ("showMsaaRole", _("MSAA role"), native.get("msaa_role")),
        ]
        if enabled("showTagSummary"):
            summary = {
                "tag": aria.get("tag", {}).get("value"),
                "captured_ia2_attributes": len(aria.get("raw_attributes", {})),
                "derived_attributes": len(aria.get("derived_attributes", {})),
            }
            identity.append((_("Tag summary"), _observation(summary)))
        for setting, label, value in options:
            if enabled(setting):
                identity.append((label, _observation(value)))
        if identity:
            sections.append((_("Identity and roles"), identity))

        if enabled("showAriaDetails"):
            rows: List[Row] = []
            for key in ("description", "keyboard_shortcut", "states", "position_info", "heading_level"):
                if key in native:
                    rows.append((key, _observation(native[key])))
            for key in sorted(aria):
                if key not in {
                    "tag",
                    "explicit_role",
                    "native_role",
                    "nvda_role",
                    "final_role",
                    "raw_attributes",
                    "derived_attributes",
                }:
                    rows.append((key, _observation(aria[key], "ia2_attribute")))
            for group in ("visible_label", "language", "form", "table", "composite"):
                data = context.get(group)
                if not isinstance(data, dict):
                    continue
                captured = cast(Dict[str, Any], data)
                if "availability" in captured:
                    rows.append((group, _observation(captured, "dom")))
                else:
                    for key in sorted(captured):
                        rows.append((group + "." + key, _observation(captured[key])))
            if rows:
                sections.append((_("Accessibility and ARIA"), rows))

        if enabled("showInteractivity"):
            rows = [(_("DOM availability"), _value(dom.get("availability", "unavailable")))]
            for key, value in sorted(dom.get("properties", {}).items()):
                rows.append((key, _observation(value, "dom")))
            if dom.get("aria_idrefs"):
                rows.append((_("DOM references"), _observation(dom["aria_idrefs"], "dom")))
            sections.append((_("Interaction and DOM"), rows))

        if enabled("showLayoutAndContrast"):
            layout = snapshot.get("layout", {})
            rows = [(_("Layout availability"), _value(layout.get("availability", "unavailable")))]
            for key in ("bounds", "viewport_intersection", "visibility", "styles", "contrast"):
                if key in layout:
                    rows.append((key, _observation(layout[key], "dom")))
            sections.append((_("Layout and appearance"), rows))

        if enabled("showAccessibilityAudit"):
            rows = []
            for item in snapshot.get("audit", []):
                status = STATUS_LABELS.get(item.get("status", ""), _("unknown"))
                reason = str(item.get("message_key") or "")
                message = FINDING_MESSAGES.get(reason, reason)
                text = status + ": " + message + "; " + _("source: {}").format(item.get("source"))
                text += "; WCAG " + ", ".join(item.get("wcag_refs", []))
                text += "; " + _("evidence: {}").format(_value(item.get("evidence", {})))
                rows.append((item.get("rule_id", ""), text))
            if rows:
                sections.append((_("Diagnostic checks"), rows))

        technical: List[Row] = []
        for setting, label, mapping, source in [
            ("showRawAttributes", _("Raw IA2 attributes"), aria.get("raw_attributes", {}), "ia2_attribute"),
            (
                "showDerivedAttributes",
                _("Attributes derived from NVDA states"),
                aria.get("derived_attributes", {}),
                "derived",
            ),
            ("showRawAttributes", _("DOM attributes"), dom.get("attributes", {}), "dom"),
        ]:
            if enabled(setting):
                for key, value in sorted(mapping.items()):
                    technical.append((label + "." + key, _observation(value, source)))
        if technical:
            sections.append((_("Technical attributes"), technical))

        if include_ancestors and enabled("showAncestors"):
            rows = []
            for number, ancestor in enumerate(context.get("ancestors", []), 1):
                for heading, child_rows in self._sections(ancestor, active_fields, include_ancestors=False):
                    for label, text in child_rows:
                        rows.append((_("Ancestor {}").format(number) + ": " + heading + " / " + label, text))
            if rows:
                sections.append((_("Ancestor elements"), rows))
        return sections

    def buildReport(self, data: Dict[str, Any]) -> str:
        snapshot = self._snapshot(data)
        result = [
            "<html><head><meta charset='utf-8'></head><body><main>",
            "<h1>" + html.escape(_("Detailed Element Info")) + "</h1>",
            "<p>" + html.escape(SCOPE_TEXT) + "</p>",
        ]
        reason = snapshot.get("availability", {}).get("bridge_reason")
        if reason:
            result.append("<p>" + html.escape(_("Bridge availability: {}").format(reason)) + "</p>")
        sections = self._sections(snapshot)
        if not sections:
            result.append("<p>" + html.escape(_("No fields selected in settings")) + "</p>")
        for heading, rows in sections:
            result.extend(["<h2>" + html.escape(heading) + "</h2>", "<ul>"])
            for label, value in rows:
                result.append("<li>" + html.escape(label) + ": " + html.escape(value) + "</li>")
            result.append("</ul>")
        result.append("<p>" + html.escape(_("Press Esc to close this message")) + "</p></main></body></html>")
        return "".join(result)

    def buildMarkdownReport(self, data: Dict[str, Any]) -> str:
        snapshot = self._snapshot(data)
        result = ["# " + _markdown(_("Detailed Element Info")), "", _markdown(SCOPE_TEXT), ""]
        reason = snapshot.get("availability", {}).get("bridge_reason")
        if reason:
            result.extend([_markdown(_("Bridge availability: {}").format(reason)), ""])
        sections = self._sections(snapshot)
        if not sections:
            result.append(_markdown(_("No fields selected in settings")))
        for heading, rows in sections:
            result.extend(["## " + _markdown(heading), ""])
            result.extend("- " + _markdown(label) + ": " + _markdown(value) for label, value in rows)
            result.append("")
        return "\n".join(result).rstrip() + "\n"
