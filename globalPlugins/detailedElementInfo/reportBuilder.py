# -*- coding: utf-8 -*-

from .config import getConfig, getBool


class ReportBuilder:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def buildReport(self, obj):
        cfg = getConfig()

        lines = [
            _("Detailed Element Info"),
            "",
            _("Current element"),
            "",
        ]

        lines.extend(self._formatElement(obj, cfg))

        if getBool(cfg, "showAncestors"):
            ancestors = self.analyzer.ancestors(obj)

            if ancestors:
                lines.append("")
                lines.append(_("Ancestor elements"))

                for index, ancestor in enumerate(ancestors, start=1):
                    lines.append("")
                    lines.append(_("Ancestor {}").format(index))
                    lines.extend(self._formatElement(ancestor, cfg))

        lines.extend(["", "", _("Press Esc to close this message")])

        return "\n".join(lines)

    def _formatElement(self, obj, cfg):
        data = self.analyzer.analyze(obj)

        rawAttrs = data["rawAttrs"]
        derivedAttrs = data["derivedAttrs"]
        tag = data["tag"]
        displayTag = tag.upper() if tag else "?"

        lines = []

        if getBool(cfg, "showTagSummary"):
            totalAttrs = len(rawAttrs) + len(derivedAttrs)

            lines.append(
                _("{} tag has {} attributes").format(
                    displayTag,
                    totalAttrs,
                )
            )

        if getBool(cfg, "showAccessibleName"):
            name = data["accessibleName"]

            if name is None:
                nameText = _("unavailable")
            elif name == "":
                nameText = _("empty")
            else:
                nameText = name

            lines.append(_("Accessible name: {}").format(nameText))

        if getBool(cfg, "showNameSource"):
            lines.append(
                _("Name source: {}").format(data["nameSource"])
            )

        if getBool(cfg, "showNameSourceConfidence"):
            lines.append(
                _("Name source confidence: {}").format(data["nameConfidence"])
            )

        if getBool(cfg, "showDomTag"):
            lines.append(
                _("DOM tag: {}").format(tag if tag else _("unknown"))
            )

        if getBool(cfg, "showDomPath"):
            domPath = data["domPath"] or _("unknown")
            lines.append(_("DOM path: {}").format(domPath))

        if getBool(cfg, "showExplicitRole"):
            explicitRole = data["explicitRole"] or _("none")
            lines.append(_("Explicit ARIA role: {}").format(explicitRole))

        if getBool(cfg, "showNativeRole"):
            nativeRole = data["nativeRole"] or _("none detected")
            lines.append(_("Native HTML role: {}").format(nativeRole))

        if getBool(cfg, "showNvdaRole"):
            nvdaRole = data["nvdaRole"] or _("unknown")
            lines.append(_("NVDA role: {}").format(nvdaRole))

        if getBool(cfg, "showFinalRole"):
            lines.append(
                _("Final inferred role: {}").format(data["finalRole"])
            )

        if data["headingLevel"]:
            lines.append(
                _("Heading level: {}").format(data["headingLevel"])
            )

        if getBool(cfg, "showSemanticSource"):
            lines.append(
                _("Semantic source: {}").format(data["semanticSource"])
            )

        if getBool(cfg, "showNativeSemanticMismatch"):
            lines.append(
                _("Native semantic mismatch: {}").format(
                    data["nativeSemanticMismatch"]
                )
            )

        if getBool(cfg, "showRawAttributes") and rawAttrs:
            lines.append("")
            lines.append(_("Raw IA2 attributes:"))

            for key in sorted(rawAttrs):
                lines.append(
                    "  {}={}".format(
                        key,
                        self._shorten(rawAttrs[key]),
                    )
                )

        if getBool(cfg, "showDerivedAttributes") and derivedAttrs:
            lines.append("")
            lines.append(_("Attributes derived from NVDA states:"))

            for key in sorted(derivedAttrs):
                lines.append(
                    "  {}={}".format(
                        key,
                        self._shorten(derivedAttrs[key]),
                    )
                )

        if getBool(cfg, "showMsaaRole") and data["msaaRole"] is not None:
            lines.append(
                _("MSAA role: {}").format(
                    self._formatMsaaRole(data["msaaRole"])
                )
            )

        if not lines:
            lines.append(_("No fields selected in settings"))

        return lines

    def _shorten(self, value, limit=300):
        value = str(value)

        if len(value) <= limit:
            return value

        return value[:limit] + "..."

    def _formatMsaaRole(self, value):
        if isinstance(value, int):
            return "0x{:X}".format(value)

        return str(value)