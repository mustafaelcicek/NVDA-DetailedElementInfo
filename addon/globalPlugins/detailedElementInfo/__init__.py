# -*- coding: utf-8 -*-

import sys
import os
import copy
import uuid
from collections import OrderedDict

addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

import globalPluginHandler  # noqa: E402
import addonHandler  # noqa: E402
import api  # noqa: E402
import ui  # noqa: E402
import textInfos  # noqa: E402
import gui  # noqa: E402
from scriptHandler import script  # noqa: E402

addonHandler.initTranslation()

from .config import ensureConfigSpec  # noqa: E402
from .settingsPanel import DetailedElementInfoSettingsPanel  # noqa: E402
from .elementAnalyzer import ElementAnalyzer  # noqa: E402
from .reportBuilder import ReportBuilder  # noqa: E402


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("Detailed Element Info")

    def __init__(self):
        super().__init__()
        ensureConfigSpec()
        self._current_generation = 0
        self._is_alive = True
        self._report_snapshots = OrderedDict()
        self._ai_generation = 0

        if DetailedElementInfoSettingsPanel not in gui.settingsDialogs.NVDASettingsDialog.categoryClasses:
            gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(DetailedElementInfoSettingsPanel)

        self.analyzer = ElementAnalyzer()
        self.reportBuilder = ReportBuilder(self.analyzer)

        from .config import getBool, getConfig

        if getBool(getConfig(), "advancedSupport"):
            from . import server

            server.start_server_in_background()

    def terminate(self):
        self._is_alive = False
        self._current_generation += 1
        self._report_snapshots.clear()
        self._ai_generation += 1
        if DetailedElementInfoSettingsPanel in gui.settingsDialogs.NVDASettingsDialog.categoryClasses:
            gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(DetailedElementInfoSettingsPanel)
        try:
            from . import server

            server.cancel_active_request(reason="plugin_terminated")
            server.stop_server()
        except Exception:
            pass

        super().terminate()

    def event_foreground(self, obj, nextHandler):
        nextHandler()

    @script(
        description=_("Show focused element details"),
        gesture="kb:NVDA+shift+f1",
        speakOnDemand=True,
    )
    def script_showElementInfo(self, gesture):
        self._collectSnapshot(self._showSnapshot)

    def _collectSnapshot(self, on_ready):
        self._current_generation += 1
        current_gen = self._current_generation
        import time

        captured_at_ms = time.time() * 1000

        try:
            from . import server

            server.cancel_active_request(reason="superseded")
        except Exception:
            pass

        obj = self._getCurrentObject()
        if obj is None:
            ui.message(_("Element not found"))
            return

        from .config import getBool, getConfig

        cfg = getConfig()
        advanced_support = getBool(cfg, "advancedSupport")
        show_ancestors = getBool(cfg, "showAncestors")

        # Capture target ONCE on UI thread
        analyzed_data = self.analyzer.analyze(obj)
        snapshot = analyzed_data.get("snapshot")

        if not self._snapshotLooksLikeHtmlOrAccessible(snapshot, analyzed_data):
            ui.message(_("No HTML or accessibility element information found"))
            return

        # Freeze ancestors on UI thread if configured
        frozen_ancestors = []
        if show_ancestors:
            try:
                for ancestor in self.analyzer.ancestors(obj, maxDepth=32):
                    frozen_ancestors.append(self.analyzer.analyze(ancestor))
            except Exception:
                pass
        snapshot["context"]["ancestors"] = [data["snapshot"] for data in frozen_ancestors]
        from .config import FIELD_OPTIONS

        snapshot["availability"]["report_fields"] = {key: getBool(cfg, key) for key, _ in FIELD_OPTIONS}

        application = snapshot.get("native", {}).get("application_name", {})
        bridge_eligible = (
            application.get("availability") == "available" and application.get("value") == "chrome"
        )
        if advanced_support and not bridge_eligible:
            snapshot["availability"]["bridge_reason"] = "unsupported_native_browser"

        # Capture expected document URL on UI thread
        expected_url = (
            self.analyzer.get_expected_document_url(obj, snapshot=snapshot)
            if advanced_support and bridge_eligible
            else None
        )
        if snapshot and isinstance(snapshot.get("target"), dict):
            snapshot["target"]["document_identity"] = {
                "url": expected_url,
            }

        from . import server

        if not advanced_support or not expected_url or not server.is_valid_url(expected_url):
            self._finishSnapshot(snapshot, on_ready, current_gen)
            return

        import threading
        import wx

        target_info = self.analyzer.build_target_info(snapshot) if snapshot else {}
        req_id = snapshot["target"]["request_id"] if snapshot else ""
        bridge_req = server.create_bridge_request(
            request_id=req_id,
            target_info=target_info,
            expected_url=expected_url,
            deadline=2.0,
            captured_at_ms=captured_at_ms,
        )

        if bridge_req is None:
            self._finishSnapshot(snapshot, on_ready, current_gen)
            return

        def fetch_and_show():
            try:
                dom_data = server.wait_for_request(bridge_req, timeout=2.0)
            except Exception:
                dom_data = None

            if dom_data and not dom_data.get("error") and snapshot:
                self.analyzer.enrich_snapshot_with_dom(snapshot, dom_data)
            elif snapshot:
                snapshot["availability"]["bridge_reason"] = bridge_req.error or bridge_req.status

            def on_ui():
                if not self._is_alive:
                    return
                if self._current_generation != current_gen:
                    return
                if bridge_req.status == "cancelled":
                    return
                self._finishSnapshot(snapshot, on_ready, current_gen)

            wx.CallAfter(on_ui)

        threading.Thread(target=fetch_and_show, daemon=True).start()

    @staticmethod
    def _auditSnapshot(snapshot):
        if isinstance(snapshot, dict):
            from .audit import evaluate

            snapshot["audit"] = evaluate(snapshot)

    def _finishSnapshot(self, snapshot, on_ready, generation):
        if not self._is_alive or generation != self._current_generation:
            return
        self._auditSnapshot(snapshot)
        on_ready(copy.deepcopy(snapshot))

    def _showSnapshot(self, snapshot):
        title = _("Detailed Element Info") + " [DEI:" + str(uuid.uuid4()) + "]"
        self._report_snapshots[title] = copy.deepcopy(snapshot)
        while len(self._report_snapshots) > 20:
            self._report_snapshots.popitem(last=False)
        try:
            ui.browseableMessage(self.reportBuilder.buildReport(snapshot), title=title, isHtml=True)
        except Exception:
            self._report_snapshots.pop(title, None)
            ui.message(_("Unable to open the element information report."))

    def _reportContext(self):
        try:
            obj = api.getForegroundObject()
        except Exception:
            return True, None
        for _depth in range(32):
            if obj is None:
                break
            try:
                name = obj.name
                if isinstance(name, str) and " [DEI:" in name and name.endswith("]"):
                    try:
                        owned = obj.processID == os.getpid()
                    except Exception:
                        return True, None
                    if owned:
                        return True, self._report_snapshots.get(name)
                    return False, None
                obj = obj.parent
            except Exception:
                return False, None
        return False, None

    @script(
        description=_("Copy focused element information as Markdown"),
        speakOnDemand=True,
    )
    def script_copyElementInfoMarkdown(self, gesture):
        is_report, snapshot = self._reportContext()
        if is_report:
            if snapshot is None:
                ui.message(_("This report snapshot is unavailable. Inspect the page element again."))
            else:
                self._copySnapshot(snapshot)
            return
        self._collectSnapshot(self._copySnapshot)

    def _copySnapshot(self, snapshot):
        try:
            copied = api.copyToClip(self.reportBuilder.buildMarkdownReport(snapshot), notify=False) is True
        except Exception:
            copied = False
        ui.message(
            _("Element information copied as Markdown.")
            if copied
            else _("Unable to copy element information.")
        )

    @script(
        description=_("Analyze current element with AI"),
        gesture="kb:alt+f1",
        speakOnDemand=True,
    )
    def script_analyzeElementAI(self, gesture):
        from .config import getBool, getConfig

        is_report, snapshot = self._reportContext()
        if not getBool(getConfig(), "advancedSupport") or not is_report:
            if gesture is not None:
                gesture.send()
            return
        if snapshot is None:
            ui.message(_("This report snapshot is unavailable. Inspect the page element again."))
            return

        frozen = copy.deepcopy(snapshot)
        generation = self._current_generation
        self._ai_generation += 1
        ai_generation = self._ai_generation
        ui.message(_("AI is analyzing. Please wait."))

        import html
        import threading
        import wx
        from . import ai_handler

        def runAnalysis():
            try:
                result = ai_handler.analyze_dom_with_gemini(frozen)
            except Exception:
                result = _("AI analysis failed.")

            def publish():
                if (
                    not self._is_alive
                    or generation != self._current_generation
                    or ai_generation != self._ai_generation
                ):
                    return
                escaped = html.escape(result).replace("\n", "<br>")
                report = (
                    "<html><head><meta charset='utf-8'></head><body><main>"
                    + "<h1>"
                    + html.escape(_("AI Analysis"))
                    + "</h1>"
                    + "<p>"
                    + html.escape(_("AI advice is advisory and does not certify WCAG conformance."))
                    + "</p>"
                    + "<p>"
                    + escaped
                    + "</p>"
                    + "<p>"
                    + html.escape(_("Press Esc to close this message"))
                    + "</p></main></body></html>"
                )
                ui.browseableMessage(report, title=_("AI Analysis"), isHtml=True)

            wx.CallAfter(publish)

        threading.Thread(target=runAnalysis, daemon=True).start()

    def _isElementInfoReportOpen(self):
        return self._reportContext()[0]

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

    def _snapshotLooksLikeHtmlOrAccessible(self, snapshot, analyzed_data):
        if not snapshot:
            return False
        aria = snapshot.get("aria", {})
        raw_attrs = aria.get("raw_attributes", {})
        if raw_attrs.get("tag") or raw_attrs.get("xml-roles"):
            return True
        native_role = snapshot.get("native", {}).get("role", {})
        if native_role.get("availability") == "available" and native_role.get("value") is not None:
            return True
        if analyzed_data.get("role"):
            return True
        return False
