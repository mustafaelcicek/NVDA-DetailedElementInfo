"""Deterministic, per-element checks over captured facts only (Python 3.7+)."""

import copy
import math
import re
from typing import Any, Dict, List, Optional, Tuple

# Deliberately bounded: unsupported roles remain unknown rather than guessed.
NAME_ROLES = {
    "button",
    "link",
    "checkbox",
    "radio",
    "combobox",
    "textbox",
    "slider",
    "spinbutton",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "tab",
    "switch",
    "searchbox",
}
NATIVE_ROLES = {
    "editabletext": "textbox",
    "graphic": "img",
    "statictext": "none",
    "radiobutton": "radio",
    "togglebutton": "button",
    "passwordedit": "textbox",
}
NON_CONTROLS = {
    "none",
    "presentation",
    "group",
    "document",
    "cell",
    "row",
    "columnheader",
    "rowheader",
    "list",
    "listitem",
    "heading",
    "img",
}


def _known(observation: Dict[str, Any]) -> bool:
    return observation.get("availability") == "available"


def _computed_role(snapshot: Dict[str, Any]) -> Optional[str]:
    obs = snapshot.get("aria", {}).get("nvda_role", {})
    if not _known(obs) or obs.get("source") != "nvda":
        return None
    raw = obs.get("value")
    if not isinstance(raw, str):
        return None
    match = re.fullmatch(r"[A-Z_]+ \(([a-z]+)\)", raw)
    if match:
        return match.group(1)
    raw = raw.strip().lower()
    role = NATIVE_ROLES.get(raw, raw)
    return role if role in NAME_ROLES | NON_CONTROLS else None


def _finding(
    rule: str, status: str, reason: str, evidence: Dict[str, Any], refs: List[str]
) -> Dict[str, Any]:
    return {
        "rule_id": rule,
        "status": status,
        "message_key": reason,
        "evidence": copy.deepcopy(evidence),
        "source": "derived",
        "wcag_refs": refs,
    }


def _normalized_label(text: str) -> str:
    # Sentence decoration is ignored; operators and numerical punctuation keep their meaning.
    text = re.sub(r"(?<!\d)[,،;؛]|[,،;؛](?!\d)", " ", text.casefold())
    text = re.sub(r"(?<=[^\W\d_])['’](?=[^\W\d_])", "", text)
    text = " ".join(text.split())
    text = text.rstrip(" :：.…?؟")
    return text if re.search(r"(?:\d|\)|\b[^\W\d_])!$", text) else text.rstrip("!")


def _name_checks(snapshot: Dict[str, Any], role: Optional[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    name = snapshot.get("native", {}).get("name", {})
    value = name.get("value") if _known(name) else None
    evidence = {"computed_role": role, "computed_name": name}
    status, reason = "unknown", "name_evidence_unavailable"
    if role in NAME_ROLES:
        if isinstance(value, str):
            status = "pass" if value.strip() else "fail"
            reason = "computed_name_present" if status == "pass" else "required_computed_name_empty"
    elif role in NON_CONTROLS:
        status, reason = "not_applicable", "role_outside_name_check"
    required = _finding("accessible_name", status, reason, evidence, ["4.1.2"])

    label = snapshot.get("context", {}).get("visible_label", {})
    label_evidence = dict(evidence, visible_label=label)
    status, reason = "unknown", "visible_label_evidence_unavailable"
    if role in NON_CONTROLS:
        status, reason = "not_applicable", "role_outside_label_check"
    elif role in NAME_ROLES:
        if label.get("applicability_evidence") == "established_no_visible_text" and not label.get(
            "truncated"
        ):
            status, reason = "not_applicable", "no_visible_text_label"
        elif _known(label) and not label.get("truncated") and isinstance(value, str):
            visible = label.get("value")
            if isinstance(visible, str) and _normalized_label(visible):
                normalized = _normalized_label(visible)
                without_parentheses = _normalized_label(re.sub(r"\s+\([^()]*\)", "", visible))
                exact = normalized in _normalized_label(value)
                ambiguous = bool(re.fullmatch(r"[^\W\d_]!(?:[?؟])?", visible.strip())) or bool(
                    re.match(r"^[^\W\d_]\s+\(", visible.strip())
                )
                if ambiguous and not exact:
                    status, reason = "unknown", "ambiguous_symbolic_label"
                else:
                    compatible = exact or (
                        bool(without_parentheses) and without_parentheses in _normalized_label(value)
                    )
                    status = "pass" if compatible else "fail"
                    reason = "visible_label_in_name" if compatible else "visible_label_missing_from_name"
    return required, _finding("label_in_name", status, reason, label_evidence, ["2.5.3"])


def _image_check(snapshot: Dict[str, Any], role: Optional[str]) -> Dict[str, Any]:
    dom = snapshot.get("dom", {})
    attrs: Dict[str, Any] = dom.get("attributes", {}) if dom.get("availability") == "available" else {}
    tag = dom.get("properties", {}).get("tag_name")
    name = snapshot.get("native", {}).get("name", {})
    value = name.get("value") if _known(name) else None
    status, reason = "unknown", "image_evidence_unavailable"
    if role == "img":
        if isinstance(value, str) and value.strip():
            filename = re.fullmatch(r"[^\s]+\.(?:png|jpe?g|gif|webp|svg|bmp)(?:\?.*)?", value.strip(), re.I)
            status, reason = (
                ("warning", "image_name_looks_like_filename")
                if filename
                else ("pass", "image_computed_name_present")
            )
        elif isinstance(value, str) and attrs.get("alt") != "":
            status, reason = "fail", "exposed_image_computed_name_empty"
        # Empty alt may express decoration; conflicting exposure needs human judgment.
    elif role in {"none", "presentation"} and tag == "img" and attrs.get("alt") == "":
        status, reason = "not_applicable", "decorative_image"
    elif role is not None and role != "img":
        status, reason = "not_applicable", "not_exposed_as_image"
    return _finding(
        "image_alternative",
        status,
        reason,
        {"computed_role": role, "computed_name": name, "declared_alt": attrs.get("alt")},
        ["1.1.1"],
    )


def _click_check(snapshot: Dict[str, Any], role: Optional[str]) -> Dict[str, Any]:
    dom = snapshot.get("dom", {})
    properties = dom.get("properties", {})
    events = properties.get("inline_events", {})
    frameworks = properties.get("framework_events", {})
    clicked = "onclick" in events or any(
        "onClick" in group for group in frameworks.values() if isinstance(group, dict)
    )
    status, reason = "unknown", "event_detection_incomplete"
    if dom.get("availability") == "available":
        if clicked and role not in NAME_ROLES:
            status, reason = "warning", "click_requires_keyboard_review"
        elif role in NAME_ROLES:
            status, reason = "not_applicable", "semantic_control_keyboard_not_checked"
    return _finding(
        "click_semantics",
        status,
        reason,
        {"computed_role": role, "inline_events": events, "framework_events": frameworks},
        ["2.1.1", "4.1.2"],
    )


def _number(value: Any) -> Optional[float]:
    if type(value) not in (int, float):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except OverflowError:
        return None


def _contrast_check(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    c: Dict[str, Any] = snapshot.get("layout", {}).get("contrast") or {}
    status, reason = "unknown", c.get("reason", "contrast_evidence_unavailable")
    evidence = dict(c)
    if c.get("inactive") is True:
        status, reason = "not_applicable", "inactive_control"
    elif c.get("text_present") is False:
        status, reason = "not_applicable", "no_direct_text"
    elif c.get("availability") == "available":
        ratio = _number(c.get("ratio"))
        size = _number(c.get("font_size_px"))
        weight = _number(c.get("font_weight"))
        if ratio is not None and 1 <= ratio <= 21 and c.get("text_present") is True:
            threshold = None
            if size is not None and size > 0:
                if size >= 24:
                    threshold = 3
                elif weight is not None:
                    threshold = 3 if size >= 56 / 3 and weight >= 700 else 4.5
            if threshold is None and ratio >= 4.5:
                threshold = 4.5
            elif threshold is None and ratio < 3:
                threshold = 3
            if threshold is not None:
                status = "pass" if ratio >= threshold else "fail"
                reason = "text_contrast_sufficient" if status == "pass" else "text_contrast_below_threshold"
                evidence["threshold"] = threshold
    return _finding("text_contrast", status, reason, evidence, ["1.4.3"])


def evaluate(snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return independent findings; never recollect, mutate or certify a page."""
    role = _computed_role(snapshot)
    required, label = _name_checks(snapshot, role)
    return [
        required,
        _image_check(snapshot, role),
        label,
        _click_check(snapshot, role),
        _contrast_check(snapshot),
    ]
