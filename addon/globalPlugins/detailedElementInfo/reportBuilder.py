# -*- coding: utf-8 -*-
#bu dosyada da filtrelemeyi farklı bir şekilde yapacağım, sürekli if koşulunda bırakmayacağım. 
from .config import getConfig, getBool
import addonHandler
addonHandler.initTranslation()
class ReportBuilder:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def buildReport(self, obj):
        cfg = getConfig()

        html = [
            "<html>",
            "<head><meta http-equiv='x-ua-compatible' content='IE=edge'></head>",
            "<body>",
            f"<h1>{_('Detailed Element Info')}</h1>",
            f"<a href='#' role='button' id='ai-btn' style='display: inline-block; padding: 5px 10px; background-color: #f0f0f0; border: 1px solid #ccc; text-decoration: none; color: black;'>{_('AI Yorumu iste')}</a>",
            "<div id='ai-result' style='margin-top: 10px; font-weight: bold;'></div>",
            f"<h2>{_('Current element')}</h2>"
        ]

        html.extend(self._formatElement(obj, cfg, heading_level="h3"))

        if getBool(cfg, "advancedSupport"):
            try:
                from . import server
                import html as html_lib
                chrome_data = server.get_latest_dom_data()
                if chrome_data and isinstance(chrome_data, dict):
                    html.append(f"<h2>{_('Aktif elementin dom öznitelikleri')}</h2>")
                    html.append("<ul>")
                    for key, value in chrome_data.items():
                        html.append(f"<li>{html_lib.escape(str(key))}={html_lib.escape(self._shorten(value))}</li>")
                    html.append("</ul>")
            except Exception:
                pass

        if getBool(cfg, "showAncestors"):
            ancestors = self.analyzer.ancestors(obj)

            if ancestors:
                html.append(f"<h2>{_('Ancestor elements')}</h2>")

                for index, ancestor in enumerate(ancestors, start=1):
                    html.append(f"<h3>{_('Ancestor {}').format(index)}</h3>")
                    html.extend(self._formatElement(ancestor, cfg, heading_level="h4"))

        html.append(f"<p><em>{_('Press Esc to close this message')}</em></p>")
        html.append("</body></html>")

        return "".join(html)

    def _formatElement(self, obj, cfg, heading_level="h3"):
        data = self.analyzer.analyze(obj)

        rawAttrs = data["rawAttrs"]
        derivedAttrs = data["derivedAttrs"]
        tag = data["tag"]
        displayTag = tag.upper() if tag else "?"

        html = ["<ul>"]

        if getBool(cfg, "showTagSummary"):
            totalAttrs = len(rawAttrs) + len(derivedAttrs)
            html.append(f"<li>{_('{} tag has {} attributes').format(displayTag, totalAttrs)}</li>")

        if getBool(cfg, "showAccessibleName"):
            name = data["accessibleName"]
            if name is None:
                nameText = _("unavailable")
            elif name == "":
                nameText = _("empty")
            else:
                nameText = name
            html.append(f"<li>{_('Accessible name: {}').format(nameText)}</li>")

        if getBool(cfg, "showNameSource"):
            html.append(f"<li>{_('Name source: {}').format(data['nameSource'])}</li>")

        if getBool(cfg, "showNameSourceConfidence"):
            html.append(f"<li>{_('Name source confidence: {}').format(data['nameConfidence'])}</li>")

        if getBool(cfg, "showDomTag"):
            html.append(f"<li>{_('DOM tag: {}').format(tag if tag else _('unknown'))}</li>")

        if getBool(cfg, "showDomPath"):
            domPath = data["domPath"] or _("unknown")
            html.append(f"<li>{_('DOM path: {}').format(domPath)}</li>")

        if getBool(cfg, "showExplicitRole"):
            explicitRole = data["explicitRole"] or _("none")
            html.append(f"<li>{_('Explicit ARIA role: {}').format(explicitRole)}</li>")

        if getBool(cfg, "showNativeRole"):
            nativeRole = data["nativeRole"] or _("none detected")
            html.append(f"<li>{_('Native HTML role: {}').format(nativeRole)}</li>")

        if getBool(cfg, "showNvdaRole"):
            nvdaRole = data["nvdaRole"] or _("unknown")
            html.append(f"<li>{_('NVDA role: {}').format(nvdaRole)}</li>")

        if getBool(cfg, "showFinalRole"):
            html.append(f"<li>{_('Final inferred role: {}').format(data['finalRole'])}</li>")

        if data["headingLevel"]:
            html.append(f"<li>{_('Heading level: {}').format(data['headingLevel'])}</li>")

        if getBool(cfg, "showSemanticSource"):
            html.append(f"<li>{_('Semantic source: {}').format(data['semanticSource'])}</li>")

        if getBool(cfg, "showNativeSemanticMismatch"):
            html.append(f"<li>{_('Native semantic mismatch: {}').format(data['nativeSemanticMismatch'])}</li>")

        if getBool(cfg, "showMsaaRole") and data["msaaRole"] is not None:
            html.append(f"<li>{_('MSAA role: {}').format(self._formatMsaaRole(data['msaaRole']))}</li>")

        html.append("</ul>")

        if getBool(cfg, "showRawAttributes") and rawAttrs:
            html.append(f"<{heading_level}>{_('Raw IA2 attributes:')}</{heading_level}><ul>")
            for key in sorted(rawAttrs):
                html.append(f"<li>{key}={self._shorten(rawAttrs[key])}</li>")
            html.append("</ul>")

        if getBool(cfg, "showDerivedAttributes") and derivedAttrs:
            html.append(f"<{heading_level}>{_('Attributes derived from NVDA states:')}</{heading_level}><ul>")
            for key in sorted(derivedAttrs):
                html.append(f"<li>{key}={self._shorten(derivedAttrs[key])}</li>")
            html.append("</ul>")

        if len(html) == 2:  # Only <ul> and </ul>
            html = [f"<p>{_('No fields selected in settings')}</p>"]

        return html

    def _shorten(self, value, limit=300):
        value = str(value)
        if len(value) <= limit:
            return value
        return value[:limit] + "..."

    def _formatMsaaRole(self, value):
        if isinstance(value, int):
            return "0x{:X}".format(value)
        return str(value)