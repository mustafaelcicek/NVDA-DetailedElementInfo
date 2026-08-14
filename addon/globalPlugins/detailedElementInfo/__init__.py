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

#aşağıdaki kısım değişecek, birkaç şey denedim ama verim alamadım.
#amacım tree'de olan elementi chrom'a gönderip ordan eşleştirme yapmaktı.
        from .config import getBool, getConfig
        if getBool(getConfig(), "advancedSupport"):
            role_obj = getattr(obj, "role", None)
            target_info = {
                "name": getattr(obj, "name", "") or "",
                "role": getattr(obj, "roleString", "") or "",
                "role_value": role_obj.value if role_obj and hasattr(role_obj, "value") else -1,
                "nvda_selector": self.analyzer.buildDomPath(obj)
            }
            
            if obj.location:
                target_info["width"] = obj.location[2]
                target_info["height"] = obj.location[3]
                
            # IA2 özelliklerinden tag, id, class gibi DOM bilgilerini çek
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
#gecikmeyi bilerek ekledim, diğer türlü odak direkt değişip element bilgisi çekmiyodu eklenti.


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
    )
    def script_analyzeElementAI(self, gesture):
        from .config import getBool, getConfig
        if not getBool(getConfig(), "advancedSupport"):
            gesture.send()
            return

        # Yalnızca Rapor penceresindeyken çalışsın
        fg = api.getForegroundObject()
        is_report = False
        
        obj = fg
        while obj:
            if obj.name == _("Detailed Element Info"):
                is_report = True
                break
            obj = obj.parent

        if not is_report:
            gesture.send()
            return

        ui.message(_("Yapay Zeka analiz ediyor, lütfen bekleyin..."))

        import threading
        import wx
        from . import server

        def _run_ai():
            try:
                res = server.get_ai_analysis()
                html_res = f"<html><head><meta http-equiv='x-ua-compatible' content='IE=edge'></head><body><h2>{_('AI Analysis')}</h2><p>{res.replace(chr(10), '<br>')}</p><p><em>{_('Press Esc to close this message')}</em></p></body></html>"
                wx.CallAfter(ui.browseableMessage, html_res, title=_("AI Analysis"), isHtml=True)
            except Exception as e:
                wx.CallAfter(ui.message, _("AI Hatası: {}").format(str(e)))
        
        threading.Thread(target=_run_ai, daemon=True).start()

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