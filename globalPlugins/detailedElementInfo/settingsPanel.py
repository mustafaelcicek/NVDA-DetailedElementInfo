# -*- coding: utf-8 -*-

import wx
import gui

from .config import FIELD_OPTIONS, getConfig


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

        for key, label in FIELD_OPTIONS:
            checkBox = wx.CheckBox(self, label=_(label))
            self._fieldCheckBoxes[key] = checkBox
            fieldsHelper.addItem(checkBox)

        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.selectAllButton = wx.Button(self, label=_("Select all"))
        self.clearAllButton = wx.Button(self, label=_("Clear all"))

        buttonsSizer.Add(self.selectAllButton, 0, wx.RIGHT, 10)
        buttonsSizer.Add(self.clearAllButton, 0)

        fieldsHelper.addItem(buttonsSizer)
        helper.addItem(fieldsGroup)

        self.selectAllButton.Bind(wx.EVT_BUTTON, self._onSelectAll)
        self.clearAllButton.Bind(wx.EVT_BUTTON, self._onClearAll)

        self._load()

    def _load(self):
        cfg = getConfig()

        for key, _label in FIELD_OPTIONS:
            try:
                value = bool(cfg[key])
            except Exception:
                value = True

            self._fieldCheckBoxes[key].SetValue(value)

    def onSave(self):
        cfg = getConfig()

        for key, _label in FIELD_OPTIONS:
            cfg[key] = self._fieldCheckBoxes[key].GetValue()

    def _onSelectAll(self, evt):
        for key, _label in FIELD_OPTIONS:
            self._fieldCheckBoxes[key].SetValue(True)

    def _onClearAll(self, evt):
        for key, _label in FIELD_OPTIONS:
            self._fieldCheckBoxes[key].SetValue(False)