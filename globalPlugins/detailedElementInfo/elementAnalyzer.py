# -*- coding: utf-8 -*-

import controlTypes

try:
    import logHandler
    log = logHandler.log
except Exception:
    log = None

from .roleMaps import (
    STATE_TO_ARIA,
    NVDA_ROLE_TO_ARIA,
    getNativeAriaRole,
    getHeadingLevel,
)


class ElementAnalyzer:
    def analyze(self, obj):
        rawAttrs = self.getRawAttrs(obj)
        derivedAttrs = self.getStateBasedAttrs(obj)

        tag = rawAttrs.get("tag", "").strip().lower()
        domPath = self.buildDomPath(obj)

        accessibleName = self.getAccessibleName(obj)
        nameSource, nameConfidence = self.getNameSource(obj, rawAttrs)

        explicitRole = self.getExplicitRole(rawAttrs)
        nativeRole = getNativeAriaRole(rawAttrs, tag)
        nvdaRole = self.getNvdaRole(obj)
        finalRole = self.getFinalRole(explicitRole, nativeRole, nvdaRole)

        semanticSource = self.getSemanticSource(explicitRole, nativeRole, tag)
        nativeSemanticMismatch = self.getNativeSemanticMismatch(
            explicitRole,
            nativeRole,
            tag,
        )

        headingLevel = getHeadingLevel(tag, rawAttrs)
        msaaRole = self.getMsaaRole(obj)

        return {
            "object": obj,
            "rawAttrs": rawAttrs,
            "derivedAttrs": derivedAttrs,
            "tag": tag,
            "domPath": domPath,
            "accessibleName": accessibleName,
            "nameSource": nameSource,
            "nameConfidence": nameConfidence,
            "explicitRole": explicitRole,
            "nativeRole": nativeRole,
            "nvdaRole": nvdaRole,
            "finalRole": finalRole,
            "semanticSource": semanticSource,
            "nativeSemanticMismatch": nativeSemanticMismatch,
            "headingLevel": headingLevel,
            "msaaRole": msaaRole,
        }

    def getRawAttrs(self, obj):
        """
        Return IA2 attributes only.

        Important: this does not include attributes derived from NVDA states.
        """
        attrs = {}

        try:
            ia2 = getattr(obj, "IA2Attributes", None)

            if ia2 is not None:
                attrs = dict(ia2)
        except Exception:
            self._logDebug("Could not read IA2Attributes")

        try:
            tag = attrs.get("tag", "")

            if tag == "a" and getattr(obj, "value", None) and "href" not in attrs:
                attrs["href"] = obj.value

            elif tag == "#document" and getattr(obj, "value", None):
                attrs["document-url"] = obj.value
        except Exception:
            self._logDebug("Could not derive href or document-url from object value")

        return attrs

    def getStateBasedAttrs(self, obj):
        """
        Return ARIA-like attributes derived from NVDA states.

        These are not raw DOM attributes.
        """
        result = {}

        try:
            states = obj.states
        except Exception:
            return result

        for stateName, ariaAttr, ariaValue in STATE_TO_ARIA:
            try:
                state = getattr(controlTypes.State, stateName, None)

                if state is not None and state in states:
                    if ariaAttr not in result:
                        result[ariaAttr] = ariaValue
            except Exception:
                self._logDebug("Could not process state: {}".format(stateName))

        return result

    def getAccessibleName(self, obj):
        try:
            name = obj.name

            if name:
                return name

            return ""
        except Exception:
            self._logDebug("Could not read accessible name")
            return None

    def getNameSource(self, obj, attrs):
        if "aria-labelledby" in attrs:
            return "aria-labelledby", "certain"

        if "aria-label" in attrs:
            return "aria-label", "certain"

        nameFrom = attrs.get("name-from", "")

        if nameFrom == "value":
            return "value", "certain"

        if nameFrom == "contents":
            return "contents", "certain"

        if nameFrom == "related element":
            return "related element", "inferred"

        if nameFrom == "attribute":
            tag = attrs.get("tag", "").strip().lower()

            if "alt" in attrs:
                return "alt", "certain"

            if "title" in attrs:
                return "title", "inferred"

            if "placeholder" in attrs:
                return "placeholder", "inferred"

            if "value" in attrs:
                if tag in ("input", "button"):
                    return "value", "certain"

                return "value", "inferred"

            return "attribute", "inferred"

        try:
            if obj.name:
                return "unknown computed source", "unknown"
        except Exception:
            pass

        return "none detected", "unknown"

    def getExplicitRole(self, attrs):
        role = attrs.get("xml-roles", "").strip()

        if not role:
            return None

        return role

    def getNvdaRole(self, obj):
        try:
            role = obj.role
        except Exception:
            self._logDebug("Could not read NVDA role")
            return None

        try:
            enumName = controlTypes.Role(role).name
        except Exception:
            return str(role)

        ariaLike = NVDA_ROLE_TO_ARIA.get(enumName)

        if ariaLike:
            return "{} ({})".format(enumName, ariaLike)

        return enumName

    def getFinalRole(self, explicitRole, nativeRole, nvdaRole):
        if explicitRole:
            return explicitRole

        if nativeRole:
            return nativeRole

        if nvdaRole:
            return nvdaRole

        return "unknown"

    def getSemanticSource(self, explicitRole, nativeRole, tag):
        if not tag:
            return "unknown"

        if explicitRole and nativeRole:
            if explicitRole.lower() == str(nativeRole).lower():
                return "redundant explicit role"

            if nativeRole in ("none", "presentation"):
                return "explicit role removes native semantics"

            return "explicit role overrides native HTML"

        if explicitRole and not nativeRole:
            return "explicit role on non-semantic element"

        if nativeRole:
            if str(nativeRole).endswith("?"):
                return "native HTML, context-dependent"

            return "native HTML"

        return "no native semantics detected"

    def getNativeSemanticMismatch(self, explicitRole, nativeRole, tag):
        if not tag:
            return "unknown"

        if not explicitRole and not nativeRole:
            return "not applicable"

        if explicitRole and not nativeRole:
            return "no native role to mismatch; explicit role used"

        if nativeRole and not explicitRole:
            return "no"

        if nativeRole and explicitRole:
            if explicitRole.lower() == str(nativeRole).lower():
                return "no; explicit role is redundant"

            return "yes; explicit role differs from native role"

        return "unknown"

    def buildDomPath(self, obj, maxDepth=25):
        parts = []
        current = obj
        depth = 0

        while current is not None and depth < maxDepth:
            depth += 1

            attrs = self.getRawAttrs(current)
            tag = attrs.get("tag", "").strip().lower()

            if not tag:
                break

            if tag == "#document":
                break

            parts.append(self.domPathSegment(attrs))

            try:
                current = current.parent
            except Exception:
                break

        parts.reverse()
        return " > ".join(parts)

    def domPathSegment(self, attrs):
        tag = attrs.get("tag", "").strip().lower()

        if not tag:
            return "unknown"

        segment = tag

        nodeId = attrs.get("id", "").strip()

        if nodeId:
            return "{}#{}".format(segment, self._escapeSelectorPart(nodeId))

        classAttr = attrs.get("class", "").strip()

        if classAttr:
            classes = [c for c in classAttr.split() if c]

            if classes:
                classPart = "".join(
                    ".{}".format(self._escapeSelectorPart(c))
                    for c in classes[:2]
                )
                return "{}{}".format(segment, classPart)

        nameAttr = attrs.get("name", "").strip()

        if nameAttr:
            return '{}[name="{}"]'.format(
                segment,
                nameAttr.replace('"', '\\"'),
            )

        roleAttr = attrs.get("xml-roles", "").strip()

        if roleAttr:
            return '{}[role="{}"]'.format(
                segment,
                roleAttr.replace('"', '\\"'),
            )

        return segment

    def ancestors(self, obj, maxDepth=20):
        result = []

        try:
            current = obj.parent
        except Exception:
            return result

        depth = 0

        while current is not None and depth < maxDepth:
            depth += 1

            try:
                attrs = self.getRawAttrs(current)
                tag = attrs.get("tag")
            except Exception:
                tag = None

            if tag:
                result.append(current)

                if tag == "#document":
                    break

            try:
                current = current.parent
            except Exception:
                break

        return result

    def getMsaaRole(self, obj):
        try:
            iaObj = getattr(obj, "IAccessibleObject", None)
            childId = getattr(obj, "IAccessibleChildID", 0)

            if iaObj:
                return iaObj.accRole(childId)
        except Exception:
            self._logDebug("Could not read MSAA role")

        return None

    def _escapeSelectorPart(self, value):
        return str(value).replace('"', '\\"')

    def _logDebug(self, message):
        if log is not None:
            try:
                log.debugWarning(message, exc_info=True)
            except Exception:
                pass