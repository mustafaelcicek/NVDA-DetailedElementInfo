# -*- coding: utf-8 -*-

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

        if not self._looksLikeHtmlOrAccessibleElement(obj):
            ui.message(_("No HTML or accessibility element information found"))
            return

        report = self.reportBuilder.buildReport(obj)
        ui.browseableMessage(report, title=_("Detailed Element Info"))

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
        """
        Avoid limiting this only to web pages via treeInterceptor.
        Some embedded browser controls or IA2 objects can expose useful
        element data even when the treeInterceptor check is not enough.
        """
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