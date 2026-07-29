# -*- coding: utf-8 -*-

import sys
import os


addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

import globalPluginHandler
import addonHandler
import api
import ui
import textInfos
import gui
from scriptHandler import script
addonHandler.initTranslation()

from .config import ensureConfigSpec
from .settingsPanel import DetailedElementInfoSettingsPanel
from .elementAnalyzer import ElementAnalyzer
from .reportBuilder import ReportBuilder


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("Detailed Element Info")

    def __init__(self):
        super().__init__()
        ensureConfigSpec()

        if DetailedElementInfoSettingsPanel not in gui.settingsDialogs.NVDASettingsDialog.categoryClasses:
            gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(
                DetailedElementInfoSettingsPanel
            )

        self.analyzer = ElementAnalyzer()
        self.reportBuilder = ReportBuilder(self.analyzer)

        from .config import getBool, getConfig
        if getBool(getConfig(), "advancedSupport"):
            from . import server
            server.start_server_in_background()

    def terminate(self):
        if DetailedElementInfoSettingsPanel in gui.settingsDialogs.NVDASettingsDialog.categoryClasses:
            gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(
                DetailedElementInfoSettingsPanel
            )

        super().terminate()

    @script(
        description=_("Show focused element details"),
        gesture="kb:NVDA+shift+f1",
        speakOnDemand=True,
    )
    def script_showElementInfo(self, gesture):
        obj = self._getCurrentObject()
        if obj is None:
            ui.message(_("Element not found"))
            return

        from .config import getBool, getConfig
        if getBool(getConfig(), "advancedSupport"):
            role_obj = getattr(obj, "role", None)
            target_info = {
                "name": getattr(obj, "name", "") or "",
                "role": getattr(obj, "roleString", "") or "",
                "role_value": role_obj.value if role_obj and hasattr(role_obj, "value") else -1,
                "nvda_selector": self.analyzer.buildDomPath(obj),
            }
            
            if obj.location:
                target_info["width"] = obj.location[2]
                target_info["height"] = obj.location[3]
                
            # Include IA2 identifiers to improve matching in the Chrome extension.
            try:
                attrs = {}
                if hasattr(obj, "IAccessible2Attributes"):
                    for attr in obj.IAccessible2Attributes:
                        if ":" in attr:
                            k, v = attr.split(":", 1)
                            attrs[k.lower()] = v
                elif hasattr(obj, "HTMLAttributes"):
                    attrs = obj.HTMLAttributes
                
                if isinstance(attrs, dict):
                    target_info["tag"] = attrs.get("tag", "")
                    target_info["id"] = attrs.get("id", "")
                    target_info["class"] = attrs.get("class", "")
            except Exception:
                pass

            from . import server
            server.request_dom_data_from_clients(target_info)
            

            import wx
            wx.CallLater(300, self._showReportDelayed)
        else:
            self._showReportDelayed()


    def _showReportDelayed(self):
        obj = self._getCurrentObject()

        if obj is None:
            ui.message(_("Element not found"))
            return

        if not self._looksLikeHtmlOrAccessibleElement(obj):
            ui.message(_("No HTML or accessibility element information found"))
            return

        report = self.reportBuilder.buildReport(obj)
        ui.browseableMessage(report, title=_("Detailed Element Info"), isHtml=True)

    @script(
        description=_("Analyze current element with AI"),
        gesture="kb:alt+f1",
        speakOnDemand=True,
    )
    def script_analyzeElementAI(self, gesture):
        from .config import getBool, getConfig

        if not getBool(getConfig(), "advancedSupport"):
            gesture.send()
            return

        if not self._isElementInfoReportOpen():
            gesture.send()
            return

        ui.message(_("AI is analyzing. Please wait."))

        import html
        import threading
        import wx
        from . import server

        def runAnalysis():
            try:
                result = server.get_ai_analysis()
                escapedResult = html.escape(str(result)).replace("\n", "<br>")
                report = (
                    "<html><head><meta http-equiv='x-ua-compatible' content='IE=edge'></head>"
                    f"<body><h2>{_('AI Analysis')}</h2><p>{escapedResult}</p>"
                    f"<p><em>{_('Press Esc to close this message')}</em></p></body></html>"
                )
                wx.CallAfter(
                    ui.browseableMessage,
                    report,
                    title=_("AI Analysis"),
                    isHtml=True,
                )
            except Exception as error:
                wx.CallAfter(ui.message, _("AI error: {}").format(str(error)))

        threading.Thread(target=runAnalysis, daemon=True).start()

    def _isElementInfoReportOpen(self):
        obj = api.getForegroundObject()

        while obj is not None:
            try:
                if obj.name == _("Detailed Element Info"):
                    return True
                obj = obj.parent
            except Exception:
                return False

        return False

    def _getCurrentObject(self):
        """
        Return the browse-mode caret object when available.
        Otherwise return the current focus object.
        """
        focus = api.getFocusObject()

        if focus is None:
            return None

        treeInterceptor = getattr(focus, "treeInterceptor", None)

        if treeInterceptor is not None and not getattr(treeInterceptor, "passThrough", True):
            try:
                info = treeInterceptor.makeTextInfo(textInfos.POSITION_CARET)
                caretObj = info.NVDAObjectAtStart

                if caretObj is not None:
                    return caretObj
            except Exception:
                # Deliberately fall back to focus object.
                pass

        return focus

    def _looksLikeHtmlOrAccessibleElement(self, obj):
        try:
            attrs = self.analyzer.getRawAttrs(obj)
        except Exception:
            return False

        if attrs.get("tag"):
            return True

        if attrs.get("xml-roles"):
            return True

        try:
            return obj.role is not None
        except Exception:
            return False
