# -*- coding: utf-8 -*-

import wx
import gui

from .config import FIELD_OPTIONS, getConfig, getBool, getString


FIELD_LABELS = {
    "showTagSummary": _("Tag summary"),
    "showAccessibleName": _("Accessible name"),
    "showNameSource": _("Name source"),
    "showNameSourceConfidence": _("Name source confidence"),
    "showDomTag": _("DOM tag"),
    "showDomPath": _("DOM path"),
    "showExplicitRole": _("Explicit ARIA role"),
    "showNativeRole": _("Native HTML role"),
    "showNvdaRole": _("NVDA role"),
    "showFinalRole": _("Final inferred role"),
    "showSemanticSource": _("Semantic source"),
    "showNativeSemanticMismatch": _("Native semantic mismatch"),
    "showRawAttributes": _("Raw IA2 attributes"),
    "showDerivedAttributes": _("Attributes derived from NVDA states"),
    "showMsaaRole": _("MSAA role"),
    "showAncestors": _("Ancestor elements"),
}


class DetailedElementInfoSettingsPanel(gui.settingsDialogs.SettingsPanel):
    title = _("Detailed Element Info")

    def makeSettings(self, settingsSizer):
        helper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)

        fieldsGroup = wx.StaticBoxSizer(
            wx.StaticBox(
                self,
                label=_("Choose which fields to show when element details are displayed."),
            ),
            wx.VERTICAL,
        )

        fieldsHelper = gui.guiHelper.BoxSizerHelper(self, sizer=fieldsGroup)

        self._fieldCheckBoxes = {}

        for key, _label in FIELD_OPTIONS:
            checkBox = wx.CheckBox(self, label=FIELD_LABELS[key])
            self._fieldCheckBoxes[key] = checkBox
            fieldsHelper.addItem(checkBox)

        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.selectAllButton = wx.Button(self, label=_("Select all"))
        self.clearAllButton = wx.Button(self, label=_("Clear all"))

        buttonsSizer.Add(self.selectAllButton, 0, wx.RIGHT, 10)
        buttonsSizer.Add(self.clearAllButton, 0)

        fieldsHelper.addItem(buttonsSizer)
        helper.addItem(fieldsGroup)

        advancedGroup = wx.StaticBoxSizer(
            wx.StaticBox(
                self,
                label=_("Advanced Support and AI"),
            ),
            wx.VERTICAL,
        )
        advancedHelper = gui.guiHelper.BoxSizerHelper(self, sizer=advancedGroup)

        self.advancedSupportCheckBox = wx.CheckBox(
            self,
            label=_("Enable Advanced Support (AI and Chrome extension)"),
        )
        advancedHelper.addItem(self.advancedSupportCheckBox)

        self.chromeExtensionInfo = wx.StaticText(
            self,
            label=_("The Chrome extension must be installed to use Advanced Support."),
        )
        advancedHelper.addItem(self.chromeExtensionInfo)

        tokenSizer = wx.BoxSizer(wx.HORIZONTAL)
        tokenLabel = wx.StaticText(self, label=_("Gemini API key:"))
        self.aiTokenTextCtrl = wx.TextCtrl(self)
        tokenSizer.Add(tokenLabel, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        tokenSizer.Add(self.aiTokenTextCtrl, 1, wx.ALL | wx.EXPAND, 5)
        advancedHelper.addItem(tokenSizer)

        helper.addItem(advancedGroup)

        self.selectAllButton.Bind(wx.EVT_BUTTON, self._onSelectAll)
        self.clearAllButton.Bind(wx.EVT_BUTTON, self._onClearAll)
        self.advancedSupportCheckBox.Bind(wx.EVT_CHECKBOX, self._onAdvancedSupportToggle)

        self._load()

    def _onAdvancedSupportToggle(self, evt):
        self.aiTokenTextCtrl.Enable(self.advancedSupportCheckBox.GetValue())

    def _load(self):
        cfg = getConfig()

        for key, _label in FIELD_OPTIONS:
            try:
                value = bool(cfg[key])
            except Exception:
                value = True

            self._fieldCheckBoxes[key].SetValue(value)

        advanced = getBool(cfg, "advancedSupport", False)
        self.advancedSupportCheckBox.SetValue(advanced)
        self.aiTokenTextCtrl.SetValue(getString(cfg, "aiToken", ""))
        self.aiTokenTextCtrl.Enable(advanced)

    def onSave(self):
        cfg = getConfig()

        for key, _label in FIELD_OPTIONS:
            cfg[key] = self._fieldCheckBoxes[key].GetValue()

        cfg["advancedSupport"] = self.advancedSupportCheckBox.GetValue()
        cfg["aiToken"] = self.aiTokenTextCtrl.GetValue()


    def _onSelectAll(self, evt):
        for key, _label in FIELD_OPTIONS:
            self._fieldCheckBoxes[key].SetValue(True)

    def _onClearAll(self, evt):
        for key, _label in FIELD_OPTIONS:
            self._fieldCheckBoxes[key].SetValue(False)
