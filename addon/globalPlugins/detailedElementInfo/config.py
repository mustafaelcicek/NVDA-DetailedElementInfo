# -*- coding: utf-8 -*-

import config as nvdaConfig


CONFIG_SECTION = "detailedElementInfo"


CONFIG_SPEC = {
    "showTagSummary": "boolean(default=True)",
    "showAccessibleName": "boolean(default=True)",
    "showNameSource": "boolean(default=True)",
    "showNameSourceConfidence": "boolean(default=True)",
    "showDomTag": "boolean(default=True)",
    "showDomPath": "boolean(default=True)",
    "showExplicitRole": "boolean(default=True)",
    "showNativeRole": "boolean(default=True)",
    "showNvdaRole": "boolean(default=True)",
    "showFinalRole": "boolean(default=True)",
    "showSemanticSource": "boolean(default=True)",
    "showNativeSemanticMismatch": "boolean(default=True)",
    "showRawAttributes": "boolean(default=True)",
    "showDerivedAttributes": "boolean(default=True)",
    "showMsaaRole": "boolean(default=True)",
    "showAncestors": "boolean(default=True)",
    "advancedSupport": "boolean(default=False)",
    "aiToken": "string(default='')",
}


DEFAULTS = {
    "showTagSummary": True,
    "showAccessibleName": True,
    "showNameSource": True,
    "showNameSourceConfidence": True,
    "showDomTag": True,
    "showDomPath": True,
    "showExplicitRole": True,
    "showNativeRole": True,
    "showNvdaRole": True,
    "showFinalRole": True,
    "showSemanticSource": True,
    "showNativeSemanticMismatch": True,
    "showRawAttributes": True,
    "showDerivedAttributes": True,
    "showMsaaRole": True,
    "showAncestors": True,
    "advancedSupport": False,
    "aiToken": "",
}


FIELD_OPTIONS = [
    ("showTagSummary", "Tag summary"),
    ("showAccessibleName", "Accessible name"),
    ("showNameSource", "Name source"),
    ("showNameSourceConfidence", "Name source confidence"),
    ("showDomTag", "DOM tag"),
    ("showDomPath", "DOM path"),
    ("showExplicitRole", "Explicit ARIA role"),
    ("showNativeRole", "Native HTML role"),
    ("showNvdaRole", "NVDA role"),
    ("showFinalRole", "Final inferred role"),
    ("showSemanticSource", "Semantic source"),
    ("showNativeSemanticMismatch", "Native semantic mismatch"),
    ("showRawAttributes", "Raw IA2 attributes"),
    ("showDerivedAttributes", "Attributes derived from NVDA states"),
    ("showMsaaRole", "MSAA role"),
    ("showAncestors", "Ancestor elements"),
]


def ensureConfigSpec():
    """
    Register this add-on's configuration schema with NVDA.
    """
    nvdaConfig.conf.spec[CONFIG_SECTION] = CONFIG_SPEC


def getConfig():
    ensureConfigSpec()
    return nvdaConfig.conf[CONFIG_SECTION]


def getBool(cfg, key, default=None):
    """
    Safe boolean config reader.

    This prevents the whole add-on from crashing if a setting key is missing
    after an add-on update or a damaged config file.
    """
    if default is None:
        default = DEFAULTS.get(key, True)

    try:
        return bool(cfg[key])
    except Exception:
        return bool(default)

def getString(cfg, key, default=""):
    try:
        return str(cfg[key])
    except Exception:
        return default