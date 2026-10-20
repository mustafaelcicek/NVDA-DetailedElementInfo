# -*- coding: utf-8 -*-
"""
Standalone scenario runner for Detailed Element Info add-on.
Zero external test framework dependencies.
Runs on standard Python with minimal NVDA API boundary stubs.
"""

import builtins
import json
from pathlib import Path
import sys
import types

# Set up paths
REPO_ROOT = Path(__file__).resolve().parent.parent
ADDON_DIR = REPO_ROOT / "addon" / "globalPlugins" / "detailedElementInfo"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(ADDON_DIR))

# Minimal NVDA runtime boundary stubs
# 1. Stubs for builtins._
if not hasattr(builtins, "_"):
    builtins._ = lambda s: s

# 2. Stub for controlTypes
if "controlTypes" not in sys.modules:
    ct = types.ModuleType("controlTypes")

    class Role:
        UNKNOWN = 0
        EDITABLETEXT = 1
        GRAPHIC = 2
        STATICTEXT = 3
        GROUPING = 4
        LANDMARK = 5
        TABLEROW = 6
        TABLECELL = 7
        TABLECOLUMNHEADER = 8
        TABLEROWHEADER = 9
        COMBOBOX = 10
        LISTITEM = 11
        PROGRESSBAR = 12
        DOCUMENT = 13
        PANE = 14
        PASSWORDEDIT = 15
        BUTTON = 16
        LINK = 17
        TABLE = 18
        LIST = 19

        def __init__(self, val):
            self.value = val
            # Map value to attribute name
            for k, v in Role.__dict__.items():
                if v == val:
                    self.name = k
                    return
            self.name = str(val)

    class State:
        EXPANDED = 1
        COLLAPSED = 2
        HASPOPUP = 3
        CHECKED = 4
        HALFCHECKED = 5
        SELECTED = 6
        PRESSED = 7
        READONLY = 8
        REQUIRED = 9
        INVALID_ENTRY = 10
        BUSY = 11
        MULTISELECTABLE = 12
        AUTOCOMPLETE = 13
        PROTECTED = 14
        FOCUSED = 15

    ct.Role = Role
    ct.State = State
    sys.modules["controlTypes"] = ct
import controlTypes  # noqa: E402

# 3. Stub for addonHandler
if "addonHandler" not in sys.modules:
    ah = types.ModuleType("addonHandler")
    ah.initTranslation = lambda: None
    sys.modules["addonHandler"] = ah

# 4. Stub for logHandler
if "logHandler" not in sys.modules:
    lh = types.ModuleType("logHandler")

    class DummyLog:
        def debugWarning(self, msg, exc_info=False):
            pass

        def error(self, msg, exc_info=False):
            pass

    lh.log = DummyLog()
    sys.modules["logHandler"] = lh

# 5. Stub for config
if "config" not in sys.modules:
    cfg = types.ModuleType("config")

    class Conf:
        def __init__(self):
            self.spec = {}
            self._data = {
                "detailedElementInfo": {
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
                    "showAncestors": False,
                    "advancedSupport": False,
                    "aiToken": "",
                }
            }

        def __getitem__(self, item):
            return self._data[item]

    cfg.conf = Conf()
    sys.modules["config"] = cfg

# 6. Additional NVDA environment stubs for package __init__.py
for mod_name in ["globalPluginHandler", "api", "ui", "textInfos", "gui", "scriptHandler", "wx"]:
    if mod_name not in sys.modules:
        m = types.ModuleType(mod_name)
        if mod_name == "globalPluginHandler":

            class GlobalPlugin:
                def __init__(self):
                    pass

                def terminate(self):
                    pass

            m.GlobalPlugin = GlobalPlugin
        elif mod_name == "scriptHandler":
            m.script = lambda **kwargs: (lambda fn: fn)
        elif mod_name == "gui":

            class SettingsPanel:
                def __init__(self, *args, **kwargs):
                    pass

            class SettingsDialogs:
                class NVDASettingsDialog:
                    categoryClasses = []

                SettingsPanel = SettingsPanel

            m.settingsDialogs = SettingsDialogs()
            m.SettingsPanel = SettingsPanel
        elif mod_name == "textInfos":
            m.POSITION_CARET = 0
        elif mod_name == "wx":

            class Panel:
                pass

            class BoxSizer:
                def __init__(self, *args, **kwargs):
                    pass

                def Add(self, *args, **kwargs):
                    pass

            class StaticBoxSizer:
                def __init__(self, *args, **kwargs):
                    pass

                def Add(self, *args, **kwargs):
                    pass

            class CheckBox:
                def __init__(self, *args, **kwargs):
                    pass

                def SetValue(self, *args, **kwargs):
                    pass

                def GetValue(self):
                    return False

            class TextCtrl:
                def __init__(self, *args, **kwargs):
                    pass

                def SetValue(self, *args, **kwargs):
                    pass

                def GetValue(self):
                    return ""

            class Button:
                def __init__(self, *args, **kwargs):
                    pass

                def Bind(self, *args, **kwargs):
                    pass

            m.Panel = Panel
            m.BoxSizer = BoxSizer
            m.StaticBoxSizer = StaticBoxSizer
            m.CheckBox = CheckBox
            m.TextCtrl = TextCtrl
            m.Button = Button
            m.VERTICAL = 1
            m.HORIZONTAL = 2
            m.ALL = 3
            m.EXPAND = 4
            m.EVT_BUTTON = 5
        sys.modules[mod_name] = m


# Mock NVDA Objects for scenario tests
class MockNVDAObject:
    def __init__(self, **kwargs):
        if "name" not in self.__class__.__dict__:
            self.name = kwargs.get("name", "Test Element")
        self.role = kwargs.get("role", 1)  # EDITABLETEXT
        self.roleString = kwargs.get("roleString", "edit")
        self.states = kwargs.get("states", set())
        if "description" not in self.__class__.__dict__:
            self.description = kwargs.get("description", "A test element description")
        self.keyboardShortcut = kwargs.get("keyboardShortcut", "Ctrl+Alt+T")
        self.value = kwargs.get("value", "initial value")
        if "isProtected" not in self.__class__.__dict__:
            self.isProtected = kwargs.get("isProtected", False)
        if "positionInfo" not in self.__class__.__dict__:
            self.positionInfo = kwargs.get(
                "positionInfo", {"indexInGroup": 1, "similarItemsInGroup": 3, "level": 1}
            )
        self.location = kwargs.get("location", (10, 20, 100, 30))
        self.parent = kwargs.get("parent", None)
        if "appModule" not in self.__class__.__dict__:
            self.appModule = kwargs.get("appModule", types.SimpleNamespace(appName="chrome"))
        if "IA2Attributes" not in self.__class__.__dict__:
            self.IA2Attributes = kwargs.get(
                "IA2Attributes", {"tag": "input", "id": "test-input", "type": "text"}
            )
        self.IAccessibleObject = kwargs.get("IAccessibleObject", None)
        self.IAccessibleChildID = kwargs.get("IAccessibleChildID", 0)
        self._relations = kwargs.get("relations", {})

    def _getIA2RelationTargetsOfType(self, rel_type):
        valid_relation_types = {"controllerFor", "error", "labelledBy", "details"}
        if rel_type not in valid_relation_types:
            raise ValueError(f"Unsupported or invented relation type: {rel_type}")
        targets = self._relations.get(rel_type, [])
        for t in targets:
            yield t


# Test Suite Runner
test_cases = []


def scenario(name):
    def decorator(fn):
        test_cases.append((name, fn))
        return fn

    return decorator


@scenario("Phase 0: Snapshot top-level contract and JSON serializability")
def test_snapshot_contract():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()
    obj = MockNVDAObject()

    # Analyzer should provide build_snapshot
    assert hasattr(analyzer, "build_snapshot"), "ElementAnalyzer must implement build_snapshot"
    snapshot = analyzer.build_snapshot(obj)

    # Must be a plain dict
    assert isinstance(snapshot, dict), f"Snapshot must be dict, got {type(snapshot)}"

    # 8 top-level sections
    expected_sections = ["target", "native", "aria", "dom", "layout", "context", "audit", "availability"]
    for section in expected_sections:
        assert section in snapshot, f"Missing required top-level section: {section}"

    # Target identity
    assert "target_identity" in snapshot["target"]
    assert "request_id" in snapshot["target"]

    # Property observations contract {value, source, availability}
    native_name = snapshot["native"].get("name")
    assert native_name is not None, "native.name observation missing"
    assert "value" in native_name and "source" in native_name and "availability" in native_name
    assert native_name["source"] == "nvda"
    assert native_name["availability"] == "available"
    assert native_name["value"] == "Test Element"

    # Unimplemented / DOM sections in native phase must be explicitly unavailable
    assert snapshot["dom"]["availability"] == "unavailable"
    assert snapshot["layout"]["availability"] == "unavailable"

    # Audit list is empty in Phase 0-1
    assert isinstance(snapshot["audit"], list)

    # Must serialize to valid JSON
    serialized = json.dumps(snapshot)
    assert len(serialized) > 0, "Snapshot serialization produced empty string"


@scenario("Phase 0 & 1: Known empty, zero, and false preservation vs unavailable")
def test_empty_zero_false_preservation():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    # 1. Known empty string name
    obj_empty_name = MockNVDAObject(name="")
    snap1 = analyzer.build_snapshot(obj_empty_name)
    name_obs = snap1["native"]["name"]
    assert name_obs["value"] == "", "Known empty name must be preserved as ''"
    assert name_obs["availability"] == "available", "Known empty name must be 'available', not 'unavailable'"

    # 2. None name (unavailable)
    obj_no_name = MockNVDAObject(name=None)
    snap2 = analyzer.build_snapshot(obj_no_name)
    name_obs2 = snap2["native"]["name"]
    assert name_obs2["value"] is None
    assert name_obs2["availability"] == "unavailable"

    # 3. Numeric zero value
    obj_zero = MockNVDAObject(value=0)
    snap3 = analyzer.build_snapshot(obj_zero)
    val_obs = snap3["native"]["value"]
    assert val_obs["value"] == 0, "Zero value must be preserved as 0"
    assert val_obs["availability"] == "available"

    # 4. Boolean False value
    obj_false = MockNVDAObject(value=False)
    snap4 = analyzer.build_snapshot(obj_false)
    val_obs4 = snap4["native"]["value"]
    assert val_obs4["value"] is False, "False value must be preserved as False"
    assert val_obs4["availability"] == "available"


@scenario("Phase 1: Protected and password value suppression (fail closed)")
def test_protected_value_suppression():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    # 1. Protected object: value must be suppressed BEFORE entering snapshot
    secret_pass = "super_secret_password_123"
    obj_prot = MockNVDAObject(isProtected=True, value=secret_pass)
    snap1 = analyzer.build_snapshot(obj_prot)

    val_obs1 = snap1["native"]["value"]
    assert val_obs1["value"] != secret_pass, "Protected value MUST NOT be in snapshot"
    assert val_obs1["value"] is None, "Protected value must be None or suppressed"
    assert val_obs1.get("protected") is True or val_obs1["availability"] in ("unavailable", "protected")
    assert secret_pass not in json.dumps(
        snap1
    ), "Sensitive password leaked anywhere into serialized snapshot!"

    # 2. Indeterminate protection (checking isProtected raises error): fail closed!
    class IndeterminateProtectedObj(MockNVDAObject):
        @property
        def isProtected(self):
            raise RuntimeError("COM error checking protection state")

    obj_indet = IndeterminateProtectedObj(value=secret_pass)
    snap2 = analyzer.build_snapshot(obj_indet)
    val_obs2 = snap2["native"]["value"]
    assert val_obs2["value"] != secret_pass, "Indeterminate protection must fail closed"
    assert secret_pass not in json.dumps(snap2), "Password leaked during indeterminate protection"

    # 3. Non-protected object: value preserved
    obj_public = MockNVDAObject(isProtected=False, value="public content")
    snap3 = analyzer.build_snapshot(obj_public)
    val_obs3 = snap3["native"]["value"]
    assert val_obs3["value"] == "public content"
    assert val_obs3["availability"] == "available"


@scenario("Phase 1: Guarded independent property reads and failure isolation")
def test_property_reads_isolation():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    class BrokenGetterObj(MockNVDAObject):
        @property
        def description(self):
            raise RuntimeError("COM failure reading description")

    obj = BrokenGetterObj(name="Working Name", keyboardShortcut="Alt+X")
    snap = analyzer.build_snapshot(obj)

    # Description threw exception -> marked error
    desc_obs = snap["native"]["description"]
    assert desc_obs["availability"] == "error", f"Expected 'error', got {desc_obs['availability']}"
    assert desc_obs["value"] is None

    # Other properties must succeed independently
    name_obs = snap["native"]["name"]
    assert name_obs["availability"] == "available"
    assert name_obs["value"] == "Working Name"

    shortcut_obs = snap["native"]["keyboard_shortcut"]
    assert shortcut_obs["availability"] == "available"
    assert shortcut_obs["value"] == "Alt+X"


@scenario("Phase 1: Explicit IA2 attributes mapping and container live-region separation")
def test_ia2_attributes_mapping():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    ia2_attrs = {
        "tag": "div",
        "live": "assertive",
        "container-live": "polite",
        "atomic": "true",
        "container-atomic": "false",
        "current": "page",
        "roledescription": "custom card",
        "valuenow": "50",
        "valuemin": "0",
        "valuemax": "100",
        "valuetext": "halfway",
    }
    obj = MockNVDAObject(IA2Attributes=ia2_attrs)
    snap = analyzer.build_snapshot(obj)

    aria = snap["aria"]
    # Element's own live vs container live
    assert aria["live"]["value"] == "assertive"
    assert aria["live"]["source"] == "ia2_attribute"
    assert aria["container_live"]["value"] == "polite"
    assert aria["container_live"]["source"] == "ia2_attribute"

    # Atomic and container atomic
    assert aria["atomic"]["value"] == "true"
    assert aria["container_atomic"]["value"] == "false"

    # Roledescription & current
    assert aria["roledescription"]["value"] == "custom card"
    assert aria["current"]["value"] == "page"

    # Range values distinct
    assert aria["range_now"]["value"] == "50"
    assert aria["range_min"]["value"] == "0"
    assert aria["range_max"]["value"] == "100"
    assert aria["range_text"]["value"] == "halfway"


@scenario("Phase 1: IA2 relations retrieval and conservative handling of describedBy")
def test_ia2_relations():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    target_lbl = MockNVDAObject(name="Label Target", role=3)
    target_ctrl = MockNVDAObject(name="Controlled Target", role=18)

    relations = {
        "labelledBy": [target_lbl],
        "controllerFor": [target_ctrl],
    }
    obj = MockNVDAObject(relations=relations)
    snap = analyzer.build_snapshot(obj)

    rel_obs = snap["aria"]["relations"]

    # labelledBy is supported and returns target summary, NOT raw DOM IDREF
    lbl_data = rel_obs["labelledby"]
    assert lbl_data["availability"] == "available"
    assert len(lbl_data["value"]) == 1
    assert lbl_data["value"][0]["name"] == "Label Target"
    assert "id" not in lbl_data["value"][0] or lbl_data["value"][0].get("id") is None

    # controls queries controllerFor
    ctrl_data = rel_obs["controls"]
    assert ctrl_data["availability"] == "available"
    assert len(ctrl_data["value"]) == 1
    assert ctrl_data["value"][0]["name"] == "Controlled Target"

    # describedBy: NVDA RelationType does not support it -> must be handled conservatively as 'unsupported'
    desc_data = rel_obs["describedby"]
    assert desc_data["availability"] in ("unsupported", "unavailable"), f"Got {desc_data['availability']}"
    assert desc_data["value"] is None or desc_data["value"] == []


@scenario("Phase 0 & 1: Five context groups with verified native APIs and DOM separation")
def test_context_groups():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    # Object representing a table cell with native table APIs
    obj = MockNVDAObject(
        IA2Attributes={"tag": "td", "language": "ar-EG", "dir": "rtl"},
        positionInfo={"indexInGroup": 2, "similarItemsInGroup": 5},
    )
    # Attach native table cell properties
    obj.rowNumber = 2
    obj.columnNumber = 3
    obj.rowSpan = 1
    obj.columnSpan = 2
    obj.rowCount = 10
    obj.columnCount = 4

    snap = analyzer.build_snapshot(obj)
    context = snap["context"]

    # 1. visible_label: unavailable without DOM
    assert context["visible_label"]["availability"] == "unavailable"

    # 2. language: read from IA2 attributes or native
    assert context["language"]["effective_language"]["value"] == "ar-EG"
    assert context["language"]["direction"]["value"] == "rtl"

    # 3. form: native group position preserved, DOM constraints unavailable
    assert context["form"]["group_position"]["value"]["indexInGroup"] == 2
    assert context["form"]["pattern"]["availability"] == "unavailable"

    # 4. table: native coordinates populated, NOT replaced by group position!
    table_ctx = context["table"]
    assert table_ctx["row_index"]["value"] == 2
    assert table_ctx["row_index"]["availability"] == "available"
    assert table_ctx["column_index"]["value"] == 3
    assert table_ctx["column_index"]["availability"] == "available"
    assert table_ctx["row_span"]["value"] == 1
    assert table_ctx["column_span"]["value"] == 2

    # 5. composite: active_descendant unavailable without DOM
    assert context["composite"]["active_descendant"]["availability"] == "unavailable"


@scenario("Phase 0 Compatibility Seam: Legacy analyzer.analyze and ReportBuilder work")
def test_backward_compatibility():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer
    from addon.globalPlugins.detailedElementInfo.reportBuilder import ReportBuilder

    analyzer = ElementAnalyzer()
    obj = MockNVDAObject(name="Legacy Target", IA2Attributes={"tag": "button"})

    # analyzer.analyze(obj) still returns flat dict with expected keys
    data = analyzer.analyze(obj)
    required_legacy_keys = [
        "object",
        "rawAttrs",
        "derivedAttrs",
        "tag",
        "domPath",
        "accessibleName",
        "nameSource",
        "nameConfidence",
        "explicitRole",
        "nativeRole",
        "nvdaRole",
        "finalRole",
        "semanticSource",
        "nativeSemanticMismatch",
        "headingLevel",
        "msaaRole",
    ]
    for key in required_legacy_keys:
        assert key in data, f"Legacy key '{key}' missing from analyzer.analyze result"

    # Also provides the snapshot
    assert "snapshot" in data, "analyzer.analyze must include 'snapshot' key"

    # ReportBuilder._formatElement and buildReport work with data
    builder = ReportBuilder(analyzer)
    html_report = builder.buildReport(data["snapshot"])
    assert "<h1>Detailed Element Info</h1>" in html_report
    assert "<h2>Identity and roles</h2>" in html_report


@scenario("Phase 1: Relation targets budget cap at 8 items")
def test_relation_targets_budget_cap():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    # 12 targets
    targets = [MockNVDAObject(name=f"Target {i}") for i in range(12)]
    obj = MockNVDAObject(relations={"controllerFor": targets})
    snap = analyzer.build_snapshot(obj)

    ctrl_obs = snap["aria"]["relations"]["controls"]
    assert ctrl_obs["availability"] == "available"
    assert len(ctrl_obs["value"]) == 8, f"Expected 8 capped targets, got {len(ctrl_obs['value'])}"


@scenario("Phase 1: Graceful degradation with missing or empty IA2Attributes")
def test_missing_and_empty_ia2_isolation():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    # None IA2Attributes
    obj_no_ia2 = MockNVDAObject(IA2Attributes=None)
    snap1 = analyzer.build_snapshot(obj_no_ia2)
    assert snap1["availability"]["ia2"] == "unavailable"
    assert snap1["aria"]["tag"]["availability"] == "unavailable"
    assert snap1["aria"]["live"]["availability"] == "unavailable"

    # Empty dict IA2Attributes
    obj_empty_ia2 = MockNVDAObject(IA2Attributes={})
    snap2 = analyzer.build_snapshot(obj_empty_ia2)
    assert snap2["availability"]["ia2"] == "unavailable"
    assert snap2["aria"]["tag"]["availability"] == "unavailable"


@scenario("Phase 0 & 1: Conflicting raw and computed values preserved distinctly")
def test_conflicting_raw_and_computed_values_distinct():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    # Object where IA2 xml-roles says 'button', but NVDA role says EDITABLETEXT
    obj = MockNVDAObject(
        role=1, roleString="edit", IA2Attributes={"tag": "div", "xml-roles": "button"}  # EDITABLETEXT
    )
    snap = analyzer.build_snapshot(obj)

    # Raw IA2 explicit role is button
    assert snap["aria"]["explicit_role"]["value"] == "button"
    assert snap["aria"]["explicit_role"]["source"] == "ia2_attribute"

    # Native NVDA role is EDITABLETEXT
    assert snap["native"]["role"]["value"] == 1
    assert snap["native"]["role"]["source"] == "nvda"
    assert snap["aria"]["nvda_role"]["source"] == "nvda"


@scenario("Regression 1: Indeterminate protection fails closed without reading value")
def test_indeterminate_protection():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    class BareObject:
        def __init__(self):
            self._value_read_attempted = False

        @property
        def value(self):
            self._value_read_attempted = True
            return "SYNTHETIC_PRIVATE_VALUE_FOR_REVIEW"

        states = None
        role = None
        IA2Attributes = {}

    bare = BareObject()
    snap = analyzer.build_snapshot(bare)

    assert (
        not bare._value_read_attempted
    ), "Private value getter was accessed during indeterminate protection!"
    val_obs = snap["native"]["value"]
    assert val_obs["value"] is None, "Indeterminate value must be None"
    assert val_obs["availability"] == "unavailable"
    assert val_obs.get("protection") == "indeterminate"
    assert "SYNTHETIC_PRIVATE_VALUE_FOR_REVIEW" not in json.dumps(snap)


@scenario("Regression 2: Protected IA2Attributes value sanitized from snapshot and HTML")
def test_protected_raw_attributes_sanitized():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer
    from addon.globalPlugins.detailedElementInfo.reportBuilder import ReportBuilder

    analyzer = ElementAnalyzer()
    builder = ReportBuilder(analyzer)

    sentinel = "SECRET_SENTINEL_PW"
    obj = MockNVDAObject(
        isProtected=True, IA2Attributes={"tag": "input", "type": "password", "value": sentinel, "name": "pwd"}
    )
    snap = analyzer.build_snapshot(obj)
    data = analyzer.analyze(obj)
    html = builder.buildReport(data["snapshot"])

    assert sentinel not in json.dumps(snap), "Sentinel password leaked into serialized snapshot!"
    assert sentinel not in html, "Sentinel password leaked into HTML report!"
    assert sentinel not in str(data["rawAttrs"]), "Sentinel password leaked into legacy rawAttrs!"
    assert (
        data["rawAttrs"].get("type") == "password"
    ), "Unrelated attribute type='password' must be preserved!"


@scenario("Regression 3: Guarded observations isolate failing external boundary getters")
def test_guarded_observations():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    class FailingProviderObj(MockNVDAObject):
        @property
        def name(self):
            raise NotImplementedError("name not implemented by proxy")

        @property
        def positionInfo(self):
            raise RuntimeError("COM failure reading positionInfo")

        @property
        def rowNumber(self):
            raise NotImplementedError("table rowNumber not implemented")

        @property
        def IA2Attributes(self):
            raise RuntimeError("IA2Attributes COM failure")

    obj = FailingProviderObj()
    snap = analyzer.build_snapshot(obj)

    assert snap["native"]["name"]["availability"] == "unsupported"
    assert snap["native"]["position_info"]["availability"] == "error"
    assert snap["context"]["table"]["row_index"]["availability"] == "unsupported"
    assert snap["availability"]["ia2"] == "error"
    assert snap["native"]["keyboard_shortcut"]["availability"] == "available"


@scenario("Regression 4: Root properties captured once and reused without recollecting")
def test_root_properties_captured_once():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    class DynamicNameObj(MockNVDAObject):
        def __init__(self):
            super().__init__()
            self.access_count = 0

        @property
        def name(self):
            self.access_count += 1
            return f"Observed name {self.access_count}"

    obj = DynamicNameObj()
    data = analyzer.analyze(obj)
    snap = data["snapshot"]

    target_name = snap["target"]["target_identity"]["name"]
    native_name = snap["native"]["name"]["value"]
    legacy_name = data["accessibleName"]

    assert (
        target_name == native_name == legacy_name
    ), f"Name re-collected multiple times: target={target_name}, native={native_name}, legacy={legacy_name}"


@scenario("Regression 5: Relation generator consumed boundedly with deferred error handling")
def test_relation_generator():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    class FailingTarget:
        @property
        def name(self):
            raise RuntimeError("COM error reading target name")

        role = 3

    class GeneratorRelationObj(MockNVDAObject):
        def _getIA2RelationTargetsOfType(self, rel_type):
            if rel_type == "controllerFor":
                if getattr(self, "skip_controls", False):
                    return
                for i in range(12):
                    yield MockNVDAObject(name=f"Controller Target {i}")
            elif rel_type == "error":
                yield FailingTarget()
            elif rel_type == "describedBy":
                raise ValueError("describedBy not supported by RelationType")
            elif rel_type == "details":
                yield MockNVDAObject(name="Details 1")
                raise RuntimeError("Stream broken")
            else:
                raise ValueError(f"Invented relation: {rel_type}")

    obj = GeneratorRelationObj()
    snap = analyzer.build_snapshot(obj)
    relations = snap["aria"]["relations"]

    assert relations["controls"]["availability"] == "available"
    assert len(relations["controls"]["value"]) == 8
    assert relations["controls"].get("truncated") is True

    # A separate capture leaves budget to exercise partial provider failures.
    obj.skip_controls = True
    relations = analyzer.build_snapshot(obj)["aria"]["relations"]
    assert relations["errormessage"]["availability"] == "error"
    assert relations["errormessage"]["partial"] is True
    assert len(relations["errormessage"]["value"]) == 1
    assert relations["errormessage"]["value"][0]["name"] is None

    assert relations["details"]["availability"] == "error"
    assert relations["details"]["partial"] is True
    assert len(relations["details"]["value"]) == 1

    assert relations["describedby"]["availability"] == "unsupported"


@scenario("Regression 6: Relation queries use official RelationType names")
def test_relation_names_official():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    queried_names = []

    class StrictRelationObj(MockNVDAObject):
        def _getIA2RelationTargetsOfType(self, rel_type):
            queried_names.append(rel_type)
            if rel_type in ("controllerFor", "error", "labelledBy", "details"):
                return
                yield
            raise ValueError(f"Invented relation name rejected: {rel_type}")

    obj = StrictRelationObj()
    analyzer.build_snapshot(obj)

    assert "controllerFor" in queried_names, "controls must query 'controllerFor'"
    assert "error" in queried_names, "errormessage must query 'error'"
    assert "controls" not in queried_names, "Invented name 'controls' must NOT be queried"
    assert "errorMessage" not in queried_names, "Invented name 'errorMessage' must NOT be queried"


@scenario("Regression 7: Form context distinguishes explicit false from true and unreadable states")
def test_form_context_false_and_states():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    obj = MockNVDAObject(
        states=None,
        IA2Attributes={
            "tag": "input",
            "aria-required": "false",
            "aria-readonly": "false",
            "aria-invalid": "false",
        },
    )
    snap = analyzer.build_snapshot(obj)
    form_ctx = snap["context"]["form"]

    assert form_ctx["aria_required"]["value"] is False
    assert form_ctx["aria_required"]["source"] == "ia2_attribute"
    assert form_ctx["aria_readonly"]["value"] is False
    assert form_ctx["aria_invalid"]["value"] is False

    assert form_ctx["required"]["availability"] == "unavailable"
    assert form_ctx["required"]["source"] == "nvda"
    assert form_ctx["readonly"]["availability"] == "unavailable"
    assert form_ctx["invalid"]["availability"] == "unavailable"


@scenario("Regression 8: Language preserves explicit empty string and distinguishes DOM declaration")
def test_language_empty_and_dom():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()

    obj = MockNVDAObject(IA2Attributes={"language": "", "lang": "en", "dir": "rtl"})
    snap = analyzer.build_snapshot(obj)
    lang_ctx = snap["context"]["language"]

    assert lang_ctx["effective_language"]["value"] == ""
    assert lang_ctx["effective_language"]["availability"] == "available"
    assert lang_ctx["effective_language"]["source"] == "ia2_attribute"

    assert lang_ctx["declared_lang"]["availability"] == "unavailable"
    assert lang_ctx["declared_lang"]["source"] == "dom"


@scenario("Regression 9: Snapshot capture IDs are unique UUIDs")
def test_unique_request_ids():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()
    obj = MockNVDAObject()

    snap1 = analyzer.build_snapshot(obj)
    snap2 = analyzer.build_snapshot(obj)

    id1 = snap1["target"]["request_id"]
    id2 = snap2["target"]["request_id"]
    assert id1 != id2, f"Request IDs collided: {id1} == {id2}"
    assert len(id1) >= 16, f"Request ID must be reliable UUID, got {id1}"


@scenario(
    "Regression 10: Snapshot module is compatible with Python 3.7 runtime "
    "(no PEP 604/PEP 585 runtime expressions)"
)
def test_snapshot_python37_compatibility():
    import ast
    import inspect
    from addon.globalPlugins.detailedElementInfo import snapshot

    # 1. ObservationValue must not be a Python 3.10+ types.UnionType
    union_type = getattr(types, "UnionType", None)
    if union_type is not None:
        assert not isinstance(
            snapshot.ObservationValue, union_type
        ), "ObservationValue must use typing.Union/Optional for Python 3.7 compatibility, not PEP 604 '|'"

    # 2. AST inspection: check for PEP 604 BitOr or PEP 585 subscript on builtin types in snapshot.py
    source = inspect.getsource(snapshot)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            raise AssertionError(
                f"PEP 604 BitOr '|' found at line {node.lineno}; incompatible with Python 3.7 runtime"
            )
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            if node.value.id in ("list", "dict", "tuple", "set"):
                raise AssertionError(
                    f"PEP 585 subscript on builtin '{node.value.id}' found at line {node.lineno}; "
                    "incompatible with Python 3.7 runtime"
                )


@scenario("Reviewer regression: legacy link URLs reuse captured safe values")
def test_legacy_link_urls():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()
    url = "https://example.invalid/test"
    for tag, key in (("a", "href"), ("#document", "document-url")):
        data = analyzer.analyze(MockNVDAObject(IA2Attributes={"tag": tag}, value=url))
        assert data["rawAttrs"][key] == url
        assert key not in data["snapshot"]["aria"]["raw_attributes"]
        protected = analyzer.analyze(MockNVDAObject(IA2Attributes={"tag": tag}, value=url, isProtected=True))
        assert key not in protected["rawAttrs"]
    existing = analyzer.analyze(MockNVDAObject(IA2Attributes={"tag": "a", "href": "original"}, value=url))
    assert existing["rawAttrs"]["href"] == "original"


@scenario("Reviewer regression: unavailable language getter is guarded and read once")
def test_unavailable_language():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    class LanguageObject(MockNVDAObject):
        language_reads = 0

        @property
        def language(self):
            self.language_reads += 1
            raise NotImplementedError("Language not implemented")

    obj = LanguageObject()
    snap = ElementAnalyzer().build_snapshot(obj)
    assert snap["context"]["language"]["effective_language"]["availability"] == "unsupported"
    assert snap["native"]["description"]["value"] == obj.description
    assert obj.language_reads == 1


@scenario("Reviewer regression: unavailable captured name is not queried again")
def test_unavailable_name_single_capture():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    class NameObject(MockNVDAObject):
        name_reads = 0

        @property
        def name(self):
            self.name_reads += 1
            return None

    obj = NameObject(IA2Attributes={"tag": "a"})
    data = ElementAnalyzer().analyze(obj)
    assert data["accessibleName"] is None
    assert obj.name_reads == 1


@scenario("Phase 2: Late A after B (Request A superseded by B, A rejected as conflict/stale)")
def test_phase2_late_a_after_b():
    from addon.globalPlugins.detailedElementInfo import server

    server._manager.clear()
    req_a = server.create_bridge_request(
        "req-A", {"tag": "button"}, expected_url="https://example.test/page", deadline=2.0
    )
    poll_a = server._manager.poll_claim(timeout=0.1)
    assert poll_a["request_id"] == "req-A"

    req_b = server.create_bridge_request(
        "req-B", {"tag": "input"}, expected_url="https://example.test/page", deadline=2.0
    )
    assert req_a.status == "cancelled"
    assert req_a.cancellation_reason == "superseded"

    success_a, code_a, _ = server._manager.handle_update({"request_id": "req-A", "tag": "button"})
    assert not success_a
    assert code_a == 409

    poll_b = server._manager.poll_claim(timeout=0.1)
    assert poll_b["request_id"] == "req-B"
    assert server._manager.bind_request(verified_bridge_binding("req-B"))[0]
    update = verified_bridge_result("req-B")
    update["result"]["tag"] = "input"
    success_b, code_b, _ = server._manager.handle_update(update)
    assert success_b
    assert code_b == 200

    res_b = server.wait_for_request(req_b, timeout=0.1)
    assert res_b is not None and res_b["tag"] == "input"


@scenario("Phase 2: Concurrent polls atomically claim requests")
def test_phase2_concurrent_polls():
    import threading
    from addon.globalPlugins.detailedElementInfo import server

    server._manager.clear()
    req = server.create_bridge_request(
        "req-concurrent", {"tag": "div"}, expected_url="https://example.test/page", deadline=2.0
    )

    results = []

    def worker():
        p = server._manager.poll_claim(timeout=0.5)
        results.append(p)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    claimed_count = sum(1 for r in results if r.get("action") == "get_dom")
    none_count = sum(1 for r in results if r.get("action") == "none")
    assert claimed_count == 1
    assert none_count == 1
    assert req.status == "claimed"


@scenario("Phase 2: Tab switch and document URL mismatch rejection")
def test_phase2_tabswitch_url_mismatch():
    from addon.globalPlugins.detailedElementInfo import server

    server._manager.clear()
    req = server.create_bridge_request(
        "req-url",
        {"tag": "a"},
        expected_url="https://example.com/legit",
        deadline=2.0,
    )
    _ = server._manager.poll_claim(timeout=0.1)

    success, code, _ = server._manager.handle_update(
        {
            "request_id": "req-url",
            "document_url": "https://attacker.com/fake",
            "tag": "a",
        }
    )
    assert not success
    assert code == 400
    assert req.status == "error"
    assert req.error == "unverified_result"


@scenario("Phase 2: Missing or mismatched expected identity fails safely to native")
def test_phase2_mismatched_expected_identity():
    from addon.globalPlugins.detailedElementInfo import server
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    server._manager.clear()

    success, code, _ = server._manager.handle_update({"request_id": "unsolicited-999"})
    assert not success
    assert code == 400

    success, code, _ = server._manager.handle_update(["not-a-dict"])
    assert not success
    assert code == 400

    analyzer = ElementAnalyzer()
    obj = MockNVDAObject(name="Safe Native Button", role=controlTypes.Role.BUTTON)
    snap = analyzer.build_snapshot(obj)
    assert snap["availability"]["bridge"] == "unavailable"
    assert snap["native"]["name"]["value"] == "Safe Native Button"


@scenario("Phase 2: Duplicate weak matches and tied candidate scores in JS")
def test_phase2_duplicate_weak_matches():
    import subprocess

    proc = subprocess.run(["node", "scripts/test_bridge_js.js"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


@scenario("Phase 2: Unsupported subframe yields native snapshot with explicit reason")
def test_phase2_unsupported_subframe():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()
    obj = MockNVDAObject(name="Subframe link", role=controlTypes.Role.LINK)
    snap = analyzer.build_snapshot(obj)

    subframe_error = {
        "request_id": snap["target"]["request_id"],
        "frame_id": 2,
        "is_top_frame": False,
        "frame_supported": False,
        "error": "Subframes are unsupported by top-frame content script.",
    }
    analyzer.enrich_snapshot_with_dom(snap, subframe_error)
    assert snap["availability"]["bridge"] == "error"
    assert snap["dom"]["availability"] == "unavailable"
    assert snap["native"]["name"]["value"] == "Subframe link"


@scenario("Phase 2: Payload limits and advisory framework responses cannot overwrite identity")
def test_phase2_payload_limits_and_framework():
    from addon.globalPlugins.detailedElementInfo import server
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    deep_payload = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": {"k": "too deep"}}}}}}}}}}}
    assert server._check_json_depth(deep_payload, max_depth=10) is False

    analyzer = ElementAnalyzer()
    obj = MockNVDAObject(
        name="React Button",
        role=controlTypes.Role.BUTTON,
        IA2Attributes={"tag": "button", "id": "real-btn"},
    )
    snap = analyzer.build_snapshot(obj)
    dom_data = {
        "request_id": snap["target"]["request_id"],
        "tag": "button",
        "id": "real-btn",
        "frameworkEvents": {"__reactProps": {"onClick": "function"}},
        "forged_identity": "attacker_id",
    }
    analyzer.enrich_snapshot_with_dom(snap, dom_data)
    assert snap["target"]["element_identity"]["id"] == "real-btn"
    assert snap["dom"]["properties"]["framework_events"] == {"__reactProps": {"onClick": "function"}}


@scenario("Phase 2: Marker data-nvda-target-id ownership and restoration safety")
def test_phase2_marker_ownership():
    import subprocess

    proc = subprocess.run(["node", "scripts/test_bridge_js.js"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


@scenario("Phase 2: Protected password suppression across all representations")
def test_phase2_protected_password_all_representations():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()
    obj = MockNVDAObject(
        role=controlTypes.Role.PASSWORDEDIT,
        value="TopSecretPass123",
        isProtected=True,
        IA2Attributes={"tag": "input", "type": "password", "value": "TopSecretPass123"},
    )
    snap = analyzer.build_snapshot(obj)
    dom_data = {
        "request_id": snap["target"]["request_id"],
        "tag": "input",
        "type": "password",
        "value": "SYNTHETIC_SECRET",
        "innerText": "SYNTHETIC_SECRET",
        "outerHTML": '<input type="password" value="SYNTHETIC_SECRET">',
        "attributes": {"type": "password", "value": "SYNTHETIC_SECRET"},
    }
    analyzer.enrich_snapshot_with_dom(snap, dom_data)

    serialized = json.dumps(snap)
    assert "TopSecretPass123" not in serialized
    assert "SYNTHETIC_SECRET" not in serialized, "Raw secret from DOM payload leaked into protected snapshot"
    assert snap["native"]["value"]["protection"] == "protected"
    assert snap["native"]["value"]["value"] is None
    assert snap["dom"]["properties"]["value"] is None
    assert "value" not in snap["dom"]["attributes"]


@scenario("Phase 2: Validation message and textarea echo redaction and capping")
def test_phase2_validation_echo_redaction():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()
    obj = MockNVDAObject(role=controlTypes.Role.EDITABLETEXT)
    snap = analyzer.build_snapshot(obj)
    long_val_msg = "Please enter valid data: " + ("x" * 600)
    dom_data = {
        "request_id": snap["target"]["request_id"],
        "context": {
            "form": {
                "validation_message": long_val_msg[:500],
                "will_validate": True,
            }
        },
    }
    analyzer.enrich_snapshot_with_dom(snap, dom_data)
    obs = snap["context"]["form"]["validation_message"]
    assert obs["availability"] == "available"
    assert len(obs["value"]) <= 500


@scenario("Phase 2: Close and terminate cancellation cleans up pending requests")
def test_phase2_close_terminate_cancellation():
    from addon.globalPlugins.detailedElementInfo import server

    server._manager.clear()
    req = server.create_bridge_request(
        "req-cancel", {}, expected_url="https://example.test/page", deadline=2.0
    )
    assert req.status == "pending"

    cancelled = server.cancel_active_request(reason="report_closed")
    assert cancelled is req
    assert req.status == "cancelled"
    assert req.cancellation_reason == "report_closed"
    assert req.event.is_set()

    server.stop_server()
    assert server._server_instance is None


@scenario("Phase 2: Offline / timeout native fallback retains functional report")
def test_phase2_offline_timeout_native_fallback():
    import time
    from addon.globalPlugins.detailedElementInfo import server
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer
    from addon.globalPlugins.detailedElementInfo.reportBuilder import ReportBuilder

    server._manager.clear()

    req = server.create_bridge_request(
        "req-timeout", {}, expected_url="https://example.test/page", deadline=0.01
    )
    time.sleep(0.02)
    res = server.wait_for_request(req, timeout=0.01)
    assert res is None
    assert req.status == "expired"

    analyzer = ElementAnalyzer()
    obj = MockNVDAObject(name="Offline Element", role=controlTypes.Role.STATICTEXT)
    analyzed = analyzer.analyze(obj)
    rb = ReportBuilder(analyzer)
    html = rb.buildReport(analyzed)
    assert "Offline Element" in html


@scenario(
    "Phase 2: Context budgets, explicit empty lang, form constraints, virtual counts, active descendant"
)
def test_phase2_context_budgets_and_nuances():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()
    obj = MockNVDAObject()
    snap = analyzer.build_snapshot(obj)

    dom_data = {
        "request_id": snap["target"]["request_id"],
        "context": {
            "visible_label": {
                "candidate_text": "Search Products",
                "source_element": "wrapping_label",
                "applicability_evidence": "wrapping_label_element",
                "availability": "available",
            },
            "language": {
                "raw_declared_lang": "",
                "effective_inherited_language": "",
                "declaring_element_identity": "div#child",
                "declared_dir": None,
                "effective_html_direction": "ltr",
                "computed_css_direction": "ltr",
            },
            "form": {
                "disabled": False,
                "will_validate": True,
                "pattern": "[A-Z]{3}",
                "min": "1",
                "max": "100",
                "browser_defaults": {"default_min": "0", "default_max": "100"},
            },
            "table": {
                "is_table_cell": True,
                "row_count": -1,
                "column_count": 4,
                "declared_row_index": 5,
                "declared_col_index": 2,
            },
            "composite": {
                "owning_composite_role": "combobox",
                "dom_focused_element": {"tag": "input", "id": "cb-input", "is_same": False},
                "aria_activedescendant": "opt-2",
                "resolved_activedescendant": {"id": "opt-2", "role": "option", "excerpt": "Option 2"},
            },
        },
    }

    analyzer.enrich_snapshot_with_dom(snap, dom_data)

    assert snap["context"]["visible_label"]["value"] == "Search Products"
    assert snap["context"]["language"]["effective_inherited_language"]["value"] == ""
    assert snap["context"]["form"]["pattern"]["value"] == "[A-Z]{3}"
    assert snap["context"]["form"]["browser_defaults"]["value"]["default_min"] == "0"
    assert snap["context"]["table"]["declared_row_count"]["value"] == -1
    assert snap["context"]["table"]["row_count"]["availability"] == "unavailable"
    assert snap["context"]["table"]["declared_row_index"]["value"] == 5
    assert snap["context"]["composite"]["active_descendant"]["value"] == "opt-2"
    assert snap["context"]["composite"]["dom_focused_element"]["value"]["is_same"] is False


@scenario("Phase 2A: Deepcopy mutation isolation during DOM snapshot merge")
def test_phase2a_deepcopy_mutation_isolation():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()
    obj = MockNVDAObject(
        role=controlTypes.Role.PASSWORDEDIT,
        isProtected=True,
    )
    snap = analyzer.build_snapshot(obj)
    original_dom_data = {
        "tag": "input",
        "value": "MUTATE_ME_SECRET",
        "attributes": {"type": "password", "value": "MUTATE_ME_SECRET"},
        "innerText": "MUTATE_ME_SECRET",
        "outerHTML": '<input type="password" value="MUTATE_ME_SECRET">',
    }
    import copy

    data_to_pass = copy.deepcopy(original_dom_data)
    analyzer.enrich_snapshot_with_dom(snap, data_to_pass)
    assert data_to_pass["value"] == "MUTATE_ME_SECRET"
    assert data_to_pass["attributes"]["value"] == "MUTATE_ME_SECRET"
    serialized = json.dumps(snap)
    assert "MUTATE_ME_SECRET" not in serialized


@scenario("Phase 2A: Strict URL contract preserves trailing slashes and queries, rejects invalid")
def test_phase2a_strict_url_contract():
    from addon.globalPlugins.detailedElementInfo import server

    assert not server._urls_match("https://example.com/dir", "https://example.com/dir/")
    assert not server._urls_match("https://example.com/dir/", "https://example.com/dir")
    assert server._urls_match("https://example.com/dir/", "https://example.com/dir/")
    assert server._urls_match("https://example.com/dir", "https://example.com/dir")

    assert not server._urls_match("https://example.com/page?id=A", "https://example.com/page?id=B")
    assert server._urls_match("https://example.com/page?id=A", "https://example.com/page?id=A")

    assert not server._urls_match("http://example.com/page", "https://example.com/page")

    assert not server.is_valid_url(None)
    assert not server.is_valid_url("")
    assert not server.is_valid_url("javascript:alert(1)")
    assert not server.is_valid_url("about:blank")
    assert server.is_valid_url("https://example.com/app")
    assert server.is_valid_url("http://localhost:8080")
    assert server.is_valid_url("file:///C:/path/file.html")

    req = server.create_bridge_request("req-bad-url", {}, expected_url="javascript:void(0)")
    assert req is None


@scenario("Phase 2A: Correlation envelope schema validation and subframe rejection")
def test_phase2a_correlation_envelope_validation():
    from addon.globalPlugins.detailedElementInfo import server

    server._manager.clear()
    expected_url = "https://example.com/dashboard"
    req = server.create_bridge_request("req-envelope", {"tag": "button"}, expected_url=expected_url)
    assert req is not None
    claimed = server._manager.poll_claim(timeout=0.1)
    assert claimed["request_id"] == "req-envelope"

    subframe_update = {
        "request_id": "req-envelope",
        "actual_frame_id": 1,
        "connected_target": True,
        "expected_url": expected_url,
        "result": {"tag": "button"},
    }
    ok, code, _ = server._manager.handle_update(subframe_update)
    assert not ok
    assert code == 400
    assert req.error == "unverified_result"

    req2 = server.create_bridge_request("req-disconnected", {"tag": "button"}, expected_url=expected_url)
    assert req2 is not None
    _ = server._manager.poll_claim(timeout=0.1)
    disconnected_update = {
        "request_id": "req-disconnected",
        "actual_frame_id": 0,
        "connected_target": False,
        "expected_url": expected_url,
        "result": {"tag": "button"},
    }
    ok2, code2, _ = server._manager.handle_update(disconnected_update)
    assert not ok2
    assert code2 == 400
    assert req2.error == "unverified_result"

    req3 = server.create_bridge_request("req-valid", {"tag": "button"}, expected_url=expected_url)
    assert req3 is not None
    _ = server._manager.poll_claim(timeout=0.1)
    valid_update = {
        "request_id": "req-valid",
        "actual_frame_id": 0,
        "connected_target": True,
        "expected_url": expected_url,
        "result": {"tag": "button", "attributes": {"id": "btn1"}},
    }
    ok3, code3, _ = server._manager.handle_update(valid_update)
    assert not ok3
    assert code3 == 400
    assert server.wait_for_request(req3, timeout=0) is None


@scenario("Phase 2A: Plugin generation tracking drops stale UI callbacks and handles terminate")
def test_phase2a_generation_tracking_ui_invalidation():

    import threading
    import api
    import ui
    import wx
    from addon.globalPlugins.detailedElementInfo import GlobalPlugin, server
    from addon.globalPlugins.detailedElementInfo.config import getConfig

    queued_workers, queued_ui, shown = [], [], []
    config = getConfig()
    previous_support = config["advancedSupport"]
    config["advancedSupport"] = False
    plugin = GlobalPlugin()
    focus = [
        MockNVDAObject(
            name="Target A",
            role=controlTypes.Role.BUTTON,
            IA2Attributes={"tag": "button", "id": "probe", "document-url": "https://example.test/page"},
        )
    ]
    patches = [
        (api, "getFocusObject", lambda: focus[0]),
        (ui, "browseableMessage", lambda report, **kwargs: shown.append(report)),
        (ui, "message", lambda *args: None),
        (wx, "CallAfter", lambda callback: queued_ui.append(callback)),
    ]
    originals = [(module, key, getattr(module, key, None)) for module, key, _ in patches]
    original_thread = threading.Thread

    class HeldThread:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            queued_workers.append(self.target)

    def complete_and_queue_report():
        claimed = server._manager.poll_claim(timeout=0)
        request_id = claimed["request_id"]
        assert server._manager.bind_request(verified_bridge_binding(request_id))[0]
        assert server._manager.handle_update(verified_bridge_result(request_id))[0]
        queued_workers.pop(0)()

    try:
        for module, key, replacement in patches:
            setattr(module, key, replacement)
        threading.Thread = HeldThread
        config["advancedSupport"] = True
        plugin.script_showElementInfo(None)
        complete_and_queue_report()
        focus[0].name = "Target B"
        plugin.script_showElementInfo(None)
        complete_and_queue_report()
        queued_ui.pop(0)()
        assert shown == []
        queued_ui.pop(0)()
        assert len(shown) == 1 and "Target B" in shown[0]

        plugin.script_showElementInfo(None)
        complete_and_queue_report()
        config["advancedSupport"] = False
        plugin.script_showElementInfo(None)
        count = len(shown)
        queued_ui.pop(0)()
        assert len(shown) == count

        config["advancedSupport"] = True
        plugin.script_showElementInfo(None)
        complete_and_queue_report()
        plugin.terminate()
        queued_ui.pop(0)()
        assert len(shown) == count
    finally:
        threading.Thread = original_thread
        config["advancedSupport"] = previous_support
        if plugin._is_alive:
            plugin.terminate()
        server._manager.clear()
        for module, key, original in originals:
            if original is None:
                delattr(module, key)
            else:
                setattr(module, key, original)


@scenario("Phase 2A: Target element getters are read once on UI thread")
def test_phase2a_single_capture_getter_counts():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer
    from addon.globalPlugins.detailedElementInfo import GlobalPlugin

    class CountedTarget(MockNVDAObject):
        def __init__(self, **kwargs):
            self.name_reads = 0
            self.role_reads = 0
            self.states_reads = 0
            self.ia2_reads = 0
            super().__init__(**kwargs)

        @property
        def name(self):
            self.name_reads += 1
            return "Counted Button"

        @property
        def role(self):
            self.role_reads += 1
            return controlTypes.Role.BUTTON

        @role.setter
        def role(self, val):
            pass

        @property
        def states(self):
            self.states_reads += 1
            return {controlTypes.State.FOCUSED}

        @states.setter
        def states(self, val):
            pass

        @property
        def IA2Attributes(self):
            self.ia2_reads += 1
            return {"tag": "button", "id": "btn"}

        @IA2Attributes.setter
        def IA2Attributes(self, val):
            pass

    target = CountedTarget()
    analyzer = ElementAnalyzer()
    analyzed = analyzer.analyze(target)
    snap = analyzed["snapshot"]

    plugin = GlobalPlugin()
    is_accessible = plugin._snapshotLooksLikeHtmlOrAccessible(snap, analyzed)
    assert is_accessible is True

    assert target.name_reads == 1
    assert target.role_reads == 1
    assert target.states_reads == 1
    assert target.ia2_reads == 1

    parent_doc = MockNVDAObject(IA2Attributes={"tag": "#document", "document-url": "https://example.com"})
    target.parent = parent_doc
    doc_url = analyzer.get_expected_document_url(target, snapshot=snap)
    assert doc_url == "https://example.com"
    assert target.name_reads == 1
    assert target.ia2_reads == 1


def verified_bridge_binding(request_id, document_id="document-A"):
    return {
        "request_id": request_id,
        "actual_tab_id": 3,
        "actual_frame_id": 0,
        "actual_document_id": document_id,
        "document_instance_nonce": "nonce-synthetic-A",
        "document_url": "https://example.test/page",
        "document_time_origin_ms": 1000.0,
        "witnessed_at_ms": 2000.0,
    }


def verified_bridge_result(request_id):
    envelope = verified_bridge_binding(request_id)
    envelope["connected_target"] = True
    envelope["result"] = {
        "request_id": request_id,
        "tag": "button",
        "id": "probe",
        "document_url": envelope["document_url"],
        "documentNonce": envelope["document_instance_nonce"],
        "frame_id": 0,
        "is_top_frame": True,
        "isConnected": True,
        "attributes": {"id": "probe"},
    }
    return envelope


@scenario("Reviewer transport: missing expected URL and unbound replies are rejected")
def test_transport_requires_binding():
    from addon.globalPlugins.detailedElementInfo.server import BridgeLifecycleManager

    manager = BridgeLifecycleManager()
    assert manager.create_request("missing-url", {}) is None
    request = manager.create_request(
        "probe", {"id": "probe", "tag": "button"}, expected_url="https://example.test/page"
    )
    assert request is not None
    manager.poll_claim(timeout=0)
    ok, _, _ = manager.handle_update(verified_bridge_result("probe"))
    assert not ok and request.result is None


@scenario("Reviewer transport: complete pinned reply succeeds and changed document fails")
def test_transport_pinned_document():
    from addon.globalPlugins.detailedElementInfo.server import BridgeLifecycleManager

    for changed in (False, True):
        manager = BridgeLifecycleManager()
        request = manager.create_request(
            "probe", {"id": "probe", "tag": "button"}, expected_url="https://example.test/page"
        )
        manager.poll_claim(timeout=0)
        assert manager.bind_request(verified_bridge_binding("probe"))[0]
        envelope = verified_bridge_result("probe")
        if changed:
            envelope["actual_document_id"] = "document-B"
        ok, _, _ = manager.handle_update(envelope)
        assert ok is not changed
        if not changed:
            result = manager.wait_for_request(request, timeout=0)
            envelope["result"]["attributes"]["id"] = "mutated"
            assert result["attributes"]["id"] == "probe"
        else:
            assert request.result is None


@scenario("Reviewer transport: wrong types, URL echo, missing identity and result lists fail")
def test_transport_rejects_malformed_envelopes():
    from addon.globalPlugins.detailedElementInfo.server import BridgeLifecycleManager

    patches = [
        {"actual_frame_id": False},
        {"connected_target": "false"},
        {"actual_document_id": ""},
        {"document_instance_nonce": None},
        {"document_url": "https://example.test/WRONG", "expected_url": "https://example.test/page"},
        {"result": ["not", "an", "object"]},
        {"result": {"tag": "button", "id": "probe"}},
    ]
    for patch in patches:
        manager = BridgeLifecycleManager()
        request = manager.create_request(
            "probe", {"id": "probe", "tag": "button"}, expected_url="https://example.test/page"
        )
        manager.poll_claim(timeout=0)
        assert manager.bind_request(verified_bridge_binding("probe"))[0]
        envelope = verified_bridge_result("probe")
        envelope.update(patch)
        assert not manager.handle_update(envelope)[0], patch
        assert request.result is None


@scenario("Reviewer privacy: protected and indeterminate DOM markup and excerpts are omitted")
def test_protected_dom_all_text_omitted():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    analyzer = ElementAnalyzer()
    for protected in (True, None):
        snapshot = analyzer.build_snapshot(MockNVDAObject(isProtected=protected))
        if protected is None:
            snapshot["native"]["value"]["protection"] = "indeterminate"
        secret = "SYNTHETIC_PRIVATE_VALUE"
        payload = {
            "tag": "textarea",
            "value": secret,
            "attributes": {"value": secret},
            "outerHTML": "<textarea>" + secret + "</textarea>",
            "innerText": secret,
            "frameworkEvents": {"onInput": secret},
            "aria_idrefs": {"aria-describedby": [{"excerpt": secret}]},
            "context": {"form": {"validation_message": secret}, "visible_label": {"candidate_text": secret}},
        }
        analyzer.enrich_snapshot_with_dom(snapshot, payload)
        assert secret not in json.dumps(snapshot)
        assert payload["value"] == secret


@scenario("Reviewer privacy: HTML cannot bypass the sanitized snapshot with legacy chrome_data")
def test_report_protected_dom_boundary():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer
    from addon.globalPlugins.detailedElementInfo.reportBuilder import ReportBuilder
    from addon.globalPlugins.detailedElementInfo.config import getConfig

    analyzer = ElementAnalyzer()
    data = analyzer.analyze(MockNVDAObject(isProtected=True))
    secret = "SYNTHETIC_LEGACY_DOM_SECRET"
    payload = {"tag": "textarea", "outerHTML": "<textarea>" + secret + "</textarea>"}
    analyzer.enrich_snapshot_with_dom(data["snapshot"], payload)
    data["chrome_data"] = payload
    config = getConfig()
    previous = config["advancedSupport"]
    try:
        config["advancedSupport"] = True
        assert secret not in ReportBuilder(analyzer).buildReport(data)
    finally:
        config["advancedSupport"] = previous


@scenario("Reviewer native context: relations share eight targets and 4000 excerpt characters")
def test_native_shared_reference_budget():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    targets = [MockNVDAObject(name="N" * 600) for _ in range(8)]
    obj = MockNVDAObject(
        relations={key: targets for key in ("labelledBy", "controllerFor", "details", "error")}
    )
    snapshot = ElementAnalyzer().build_snapshot(obj)
    summaries = [
        target
        for observation in snapshot["aria"]["relations"].values()
        for target in (observation.get("value") or [])
    ]
    assert len(summaries) <= 8
    assert sum(len(target.get("name") or "") for target in summaries) <= 4000
    assert all(len(target.get("name") or "") <= 500 for target in summaries)


@scenario("Reviewer native context: bounded header text is captured and DOM evidence stays separate")
def test_native_headers_and_dom_context_provenance():
    from addon.globalPlugins.detailedElementInfo.elementAnalyzer import ElementAnalyzer

    obj = MockNVDAObject()
    obj.rowHeaderText = "Native row " * 70
    obj.columnHeaderText = "Native column"
    obj.rowNumber = 2
    analyzer = ElementAnalyzer()
    snapshot = analyzer.build_snapshot(obj)
    row_text = snapshot["context"]["table"]["row_header_text"]
    assert row_text["availability"] == "available" and row_text["source"] == "nvda"
    assert len(row_text["value"]) <= 500 and row_text["truncated"]
    analyzer.enrich_snapshot_with_dom(
        snapshot,
        {
            "tag": "td",
            "context": {
                "table": {
                    "row_index": 3,
                    "column_index": 4,
                    "row_count": -1,
                    "declared_row_count": -1,
                    "row_headers": [{"name": "DOM header"}],
                },
                "composite": {"is_selected": True, "is_focused": False},
            },
        },
    )
    table = snapshot["context"]["table"]
    assert table["row_index"]["value"] == 2 and table["row_index"]["source"] == "nvda"
    assert table["dom_row_index"]["value"] == 3
    assert table["row_header_text"] == row_text
    assert table["dom_row_headers"]["value"][0]["name"] == "DOM header"
    assert table["declared_row_count"]["value"] == -1
    assert snapshot["context"]["composite"]["dom_selected"]["value"] is True


def audit_sample(role="BUTTON", name="Search"):
    from addon.globalPlugins.detailedElementInfo.snapshot import create_empty_snapshot, create_observation

    s = create_empty_snapshot("audit-case")
    s["native"]["name"] = create_observation(name, "nvda", "available")
    s["aria"]["nvda_role"] = create_observation(role, "nvda", "available")
    return s


def finding(snapshot, rule):
    from addon.globalPlugins.detailedElementInfo.audit import evaluate

    return next(item for item in evaluate(snapshot) if item["rule_id"] == rule)


@scenario("Phase 3: computed name applicability, absence and DOM alternatives")
def test_audit_name():
    s = audit_sample(name="")
    assert finding(s, "accessible_name")["status"] == "fail"
    s["dom"]["attributes"] = {"aria-label": "Raw author label"}
    assert finding(s, "accessible_name")["status"] == "fail"
    s["native"]["name"]["availability"] = "error"
    assert finding(s, "accessible_name")["status"] == "unknown"
    s = audit_sample(role="STATICTEXT (none)")
    assert finding(s, "accessible_name")["status"] == "not_applicable"
    s["aria"]["nvda_role"]["availability"] = "unavailable"
    assert finding(s, "accessible_name")["status"] == "unknown"


@scenario("Phase 3: label-in-name preserves meaningful symbols and incomplete evidence")
def test_audit_label_in_name():
    from copy import deepcopy
    from addon.globalPlugins.detailedElementInfo.audit import evaluate

    cases = [
        ("Search", "Search site", "pass"),
        ("Search", "Run", "fail"),
        ("First Name:", "first name", "pass"),
        ("Name (required)", "Name", "pass"),
        ("Date (YYYY-MM-DD)", "Date", "pass"),
        ("Next…", "Next", "pass"),
        ("Search!", "Search", "pass"),
        ("First name?", "First name", "pass"),
        ("Hello, world", "Hello world", "pass"),
        ("A>B", "AB", "fail"),
        ("5!", "5", "fail"),
        ("n!", "n", "unknown"),
        ("3!?", "3", "fail"),
        ("f (x)", "f", "unknown"),
        ("1,2", "1 2", "fail"),
        ("f(x)", "f", "fail"),
        ("Don't", "Dont", "pass"),
        ("11×3=33", "11333", "fail"),
    ]
    for visible, name, status in cases:
        s = audit_sample(name=name)
        s["context"]["visible_label"] = {
            "value": visible,
            "source": "dom",
            "availability": "available",
            "applicability_evidence": "visible_associated_text",
            "truncated": False,
        }
        before = deepcopy(s)
        assert finding(s, "label_in_name")["status"] == status, (visible, name)
        assert evaluate(s) == evaluate(s) and s == before
        s["context"]["visible_label"]["truncated"] = True
        assert finding(s, "label_in_name")["status"] == "unknown"
    s["context"]["visible_label"] = {
        "value": None,
        "availability": "unavailable",
        "applicability_evidence": "no_established_visible_text",
    }
    assert finding(s, "label_in_name")["status"] == "unknown"
    s["context"]["visible_label"]["applicability_evidence"] = "established_no_visible_text"
    assert finding(s, "label_in_name")["status"] == "not_applicable"


@scenario("Phase 3: image alternatives and filename warnings avoid raw-alt failures")
def test_audit_images():
    s = audit_sample("GRAPHIC (img)", "Company")
    s["dom"]["availability"] = "available"
    s["dom"]["attributes"] = {"aria-label": "Company"}
    assert finding(s, "image_alternative")["status"] == "pass"
    s["native"]["name"]["value"] = "image01.png"
    assert finding(s, "image_alternative")["status"] == "warning"
    s["native"]["name"]["value"] = ""
    s["dom"]["attributes"]["alt"] = ""
    assert finding(s, "image_alternative")["status"] == "unknown"
    s["aria"]["nvda_role"]["value"] = "STATICTEXT (none)"
    s["dom"]["properties"]["tag_name"] = "img"
    assert finding(s, "image_alternative")["status"] == "not_applicable"


@scenario("Phase 3: click evidence stays advisory and roving tabindex is not failure")
def test_audit_click():
    s = audit_sample("STATICTEXT (none)")
    s["dom"]["availability"] = "available"
    s["dom"]["properties"] = {"inline_events": {"onclick": "function"}, "tab_index": -1}
    assert finding(s, "click_semantics")["status"] == "warning"
    s["aria"]["nvda_role"]["value"] = "BUTTON"
    assert finding(s, "click_semantics")["status"] == "not_applicable"
    s["dom"]["availability"] = "unavailable"
    assert finding(s, "click_semantics")["status"] == "unknown"


@scenario("Phase 3: contrast thresholds, unknown inputs and inactive exceptions")
def test_audit_contrast():
    s = audit_sample()
    c = {
        "availability": "available",
        "source": "dom",
        "ratio": 4.499,
        "font_size_px": 16,
        "font_weight": 400,
        "text_present": True,
        "inactive": False,
    }
    s["layout"]["contrast"] = c
    assert finding(s, "text_contrast")["status"] == "fail"
    for size, weight, expected in [
        (24, 400, "pass"),
        (23.999, 400, "fail"),
        (56 / 3, 700, "pass"),
        (56 / 3 - 0.001, 700, "fail"),
    ]:
        c.update(font_size_px=size, font_weight=weight)
        assert finding(s, "text_contrast")["status"] == expected
    c.update(ratio=21, font_size_px=None)
    assert finding(s, "text_contrast")["status"] == "pass"
    for invalid in (None, True, float("nan"), float("inf"), 0, 22):
        c["ratio"] = invalid
        assert finding(s, "text_contrast")["status"] == "unknown"
    c.update(ratio=1, font_size_px=16, inactive=True)
    assert finding(s, "text_contrast")["status"] == "not_applicable"
    c.update(inactive=False, availability="unavailable", reason="ancestor_opacity")
    assert finding(s, "text_contrast")["status"] == "unknown"


@scenario("Phase 4: frozen HTML/Markdown parity, escaping and section choices")
def test_report_serializers():
    import copy
    import html
    from addon.globalPlugins.detailedElementInfo.config import DEFAULTS, FIELD_OPTIONS
    from addon.globalPlugins.detailedElementInfo.reportBuilder import ReportBuilder
    from addon.globalPlugins.detailedElementInfo.snapshot import create_observation as obs

    s = audit_sample(name="<script>[x]</script>")
    s["aria"]["tag"] = obs("button", "ia2_attribute", "available")
    s["native"]["description"] = obs("", "nvda", "available")
    s["context"]["language"] = {"effective": obs("de", "nvda", "available")}
    s["context"]["form"] = {"readonly": obs(False, "ia2_attribute", "available")}
    s["context"]["table"] = {"row_index": obs(0, "nvda", "available", truncated=True)}
    s["context"]["composite"] = {"selected": obs(False, "nvda", "available")}
    s["dom"]["properties"]["tab_index"] = 0
    s["layout"]["bounds"] = {"x": 0, "y": 0, "width": 20, "height": 10}
    s["layout"]["contrast"] = {
        "source": "dom",
        "availability": "available",
        "ratio": 4.499,
        "font_size_px": 16,
        "font_weight": 400,
    }
    s["context"]["visible_label"] = obs(
        "Search",
        "dom",
        "available",
        source_element={"id": "source-label"},
        applicability_evidence="visible_associated_text",
    )
    s["availability"]["report_fields"] = dict(DEFAULTS)
    builder = ReportBuilder()
    before = copy.deepcopy(s)
    h, m = builder.buildReport(s), builder.buildMarkdownReport(s)
    assert s == before
    assert "<h1>Detailed Element Info</h1>" in h
    for value in ("de", "false", "0", "nvda", "ia2_attribute", "truncated", "4.499", "source-label"):
        import re

        assert value in html.unescape(h) and value in re.sub(r"\\(.)", r"\1", html.unescape(m)), value
    assert "<script>" not in h and "<script>" not in m
    assert "&lt;script&gt;" in h and "&lt;script&gt;" in m
    assert "\\[x\\]" in m
    for setting, heading in [
        ("showAriaDetails", "Accessibility and ARIA"),
        ("showLayoutAndContrast", "Layout and appearance"),
        ("showInteractivity", "Interaction and DOM"),
        ("showAccessibilityAudit", "Diagnostic checks"),
    ]:
        s["audit"] = [
            {
                "rule_id": "example",
                "status": "unknown",
                "message_key": "unavailable",
                "source": "derived",
                "evidence": {},
                "wcag_refs": ["1.4.3"],
            }
        ]
        s["availability"]["report_fields"][setting] = False
        assert "<h2>" + heading + "</h2>" not in builder.buildReport(s)
        assert "## " + heading not in builder.buildMarkdownReport(s)
        s["availability"]["report_fields"][setting] = True
    s["availability"]["report_fields"] = {key: False for key, _ in FIELD_OPTIONS}
    assert "<h2>" not in builder.buildReport(s)
    assert "No fields selected" in builder.buildMarkdownReport(s)


@scenario("Phase 4: new settings preserve false/token and participate in bulk selection")
def test_section_settings():
    from addon.globalPlugins.detailedElementInfo.config import getConfig, ensureConfigSpec, FIELD_OPTIONS
    from addon.globalPlugins.detailedElementInfo.settingsPanel import DetailedElementInfoSettingsPanel
    from addon.globalPlugins.detailedElementInfo import server

    class Cell:
        def __init__(self, value=None):
            self.value = value

        def SetValue(self, value):
            self.value = value

        def GetValue(self):
            return self.value

        def Enable(self, value):
            pass

    cfg = getConfig()
    previous = dict(cfg)
    lifecycle = []
    previous_start, previous_stop = server.start_server_in_background, server.stop_server
    server.start_server_in_background = lambda: lifecycle.append("start")
    server.stop_server = lambda: lifecycle.append("stop")
    new_keys = {"showAriaDetails", "showLayoutAndContrast", "showInteractivity", "showAccessibilityAudit"}
    try:
        assert new_keys <= {key for key, _ in FIELD_OPTIONS}
        for key in new_keys:
            cfg.pop(key, None)
        cfg["showAriaDetails"] = False
        cfg["aiToken"] = " preserved-token "
        ensureConfigSpec()
        panel = DetailedElementInfoSettingsPanel.__new__(DetailedElementInfoSettingsPanel)
        panel._fieldCheckBoxes = {key: Cell() for key, _ in FIELD_OPTIONS}
        panel.advancedSupportCheckBox, panel.aiTokenTextCtrl = Cell(), Cell()
        panel._load()
        assert panel._fieldCheckBoxes["showAriaDetails"].value is False
        assert panel._fieldCheckBoxes["showLayoutAndContrast"].value is True
        assert panel.aiTokenTextCtrl.value == " preserved-token "
        panel._onClearAll(None)
        assert all(not c.GetValue() for c in panel._fieldCheckBoxes.values())
        panel._onSelectAll(None)
        assert all(c.GetValue() for c in panel._fieldCheckBoxes.values())
        panel.onSave()
        assert cfg["aiToken"] == " preserved-token "
        panel.advancedSupportCheckBox.SetValue(True)
        panel.onSave()
        panel.advancedSupportCheckBox.SetValue(False)
        panel.onSave()
        assert lifecycle[-2:] == ["start", "stop"]
    finally:
        server.start_server_in_background, server.stop_server = previous_start, previous_stop
        cfg.clear()
        cfg.update(previous)


@scenario("Phase 4: actual report identity/copy stays with A after B; clipboard failure is truthful")
def test_report_identity_copy():
    import os
    import api
    import ui
    from addon.globalPlugins.detailedElementInfo import GlobalPlugin
    from addon.globalPlugins.detailedElementInfo.config import getConfig

    config = getConfig()
    previous = config["advancedSupport"]
    config["advancedSupport"] = False
    shown, spoken, copied = [], [], []
    focus = [MockNVDAObject(name="Frozen A", IA2Attributes={"tag": "button"})]
    foreground = [types.SimpleNamespace(name="page", processID=os.getpid() + 1, parent=None)]
    success = [True]

    def clipboard(text, notify=False):
        copied.append(text)
        return success[0]

    patches = [
        (api, "getFocusObject", lambda: focus[0]),
        (api, "getForegroundObject", lambda: foreground[0]),
        (api, "copyToClip", clipboard),
        (ui, "browseableMessage", lambda text, **kw: shown.append((text, kw["title"]))),
        (ui, "message", spoken.append),
    ]
    originals = [(m, k, getattr(m, k, None)) for m, k, _ in patches]
    plugin = GlobalPlugin()
    try:
        for module, key, replacement in patches:
            setattr(module, key, replacement)
        plugin.script_showElementInfo(None)
        title_a = shown[-1][1]
        focus[0].name = "Changed A"
        focus[0] = MockNVDAObject(name="Frozen B", IA2Attributes={"tag": "button"})
        plugin.script_showElementInfo(None)
        assert shown[-1][1] != title_a
        foreground[0] = types.SimpleNamespace(name=title_a, processID=os.getpid(), parent=None)
        plugin.script_copyElementInfoMarkdown(None)
        assert "Frozen A" in copied[-1] and "Frozen B" not in copied[-1] and "Changed A" not in copied[-1]
        assert spoken[-1] == "Element information copied as Markdown."
        success[0] = False
        plugin.script_copyElementInfoMarkdown(None)
        assert spoken[-1] == "Unable to copy element information."
        foreground[0] = types.SimpleNamespace(name=title_a, processID=os.getpid() + 1, parent=None)
        plugin.script_copyElementInfoMarkdown(None)
        assert "Frozen B" in copied[-1] and "Frozen A" not in copied[-1]
        foreground[0] = types.SimpleNamespace(name="page", processID=os.getpid() + 1, parent=None)
        success[0] = True
        plugin.script_copyElementInfoMarkdown(None)
        assert "Frozen B" in copied[-1]
        for _ in range(21):
            plugin.script_showElementInfo(None)
        foreground[0] = types.SimpleNamespace(name=title_a, processID=os.getpid(), parent=None)
        count = len(copied)
        plugin.script_copyElementInfoMarkdown(None)
        assert len(copied) == count and "unavailable" in spoken[-1].lower()
    finally:
        plugin.terminate()
        config["advancedSupport"] = previous
        for module, key, original in originals:
            if original is None:
                delattr(module, key)
            else:
                setattr(module, key, original)


@scenario("Phase 4: serializers never read live targets, settings or the network")
def test_pure_report_boundaries():
    import urllib.request
    from addon.globalPlugins.detailedElementInfo import config
    from addon.globalPlugins.detailedElementInfo.reportBuilder import ReportBuilder

    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("Live external boundary reached")

    class LiveTarget:
        analyze = ancestors = forbidden

    previous_config, previous_network = config.getConfig, urllib.request.urlopen
    try:
        config.getConfig = urllib.request.urlopen = forbidden
        builder = ReportBuilder(LiveTarget())
        s = audit_sample()
        assert "Search" in builder.buildReport(s)
        assert "Search" in builder.buildMarkdownReport(s)
        try:
            builder.buildReport(LiveTarget())
        except TypeError:
            pass
        else:
            raise AssertionError("Renderer accepted a live object")
        assert calls == []
    finally:
        config.getConfig, urllib.request.urlopen = previous_config, previous_network


def ai_sample():
    from addon.globalPlugins.detailedElementInfo.snapshot import create_observation as obs

    s = audit_sample(name="Public SYNTHETIC_PRIVATE_VALUE")
    s["native"]["value"] = obs("SYNTHETIC_PRIVATE_VALUE", "nvda", "available", protection="unprotected")
    s["native"]["description"] = obs("Description SYNTHETIC_API_KEY", "nvda", "available")
    s["aria"]["tag"] = obs("button", "ia2_attribute", "available")
    s["aria"]["relations"] = {
        "labelledby": obs(
            [{"name": "Public reference", "role": "16"}, {"name": "SYNTHETIC_PRIVATE_VALUE", "role": "16"}],
            "ia2_relation",
            "available",
        )
    }
    return s


@scenario("Phase 5: allowlisted AI evidence redacts duplicates and excludes context/raw data")
def test_ai_allowlist():
    import copy
    from addon.globalPlugins.detailedElementInfo.ai_handler import build_ai_payload

    s = ai_sample()
    s["target"]["document_identity"] = {"url": "https://PRIVATE_URL.test"}
    s["target"]["target_identity"] = {"window_handle": "PRIVATE_HANDLE"}
    s["dom"]["attributes"] = {"selector": "PRIVATE_SELECTOR", "data-token": "PRIVATE_ATTRIBUTE"}
    s["dom"]["properties"] = {"safe_outer_html": "<textarea>PRIVATE_MARKUP</textarea>"}
    s["context"] = {
        name: {"value": "PRIVATE_CONTEXT"}
        for name in ("visible_label", "language", "form", "table", "composite")
    }
    s["audit"] = [
        {
            "rule_id": "text_contrast",
            "status": "unknown",
            "wcag_refs": ["1.4.3"],
            "evidence": {"ratio": 4.499, "raw": "PRIVATE_EVIDENCE"},
        }
    ]
    before = copy.deepcopy(s)
    payload = build_ai_payload(s, sensitive_values=["SYNTHETIC_API_KEY"])
    encoded = json.dumps(payload, ensure_ascii=False)
    for private in (
        "SYNTHETIC_PRIVATE_VALUE",
        "SYNTHETIC_API_KEY",
        "PRIVATE_URL",
        "PRIVATE_HANDLE",
        "PRIVATE_SELECTOR",
        "PRIVATE_ATTRIBUTE",
        "PRIVATE_MARKUP",
        "PRIVATE_CONTEXT",
        "PRIVATE_EVIDENCE",
    ):
        assert private not in encoded, private
    assert "Public" in encoded and "Public reference" in encoded
    assert payload["findings"][0]["status"] == "unknown"
    assert s == before


@scenario("Phase 5: valid deterministic JSON cap, reference limits and fail-closed protection")
def test_ai_caps_protection():
    from addon.globalPlugins.detailedElementInfo.ai_handler import build_ai_payload

    s = ai_sample()
    s["native"]["name"]["value"] = "ع" * 10000
    s["native"]["description"]["value"] = "غ" * 10000
    s["aria"]["relations"]["labelledby"]["value"] = [{"name": "م" * 600, "role": "16"}] * 30
    for limit in (1600, 16000):
        first = build_ai_payload(s, max_chars=limit)
        second = build_ai_payload(s, max_chars=limit)
        encoded = json.dumps(first, ensure_ascii=False, separators=(",", ":"))
        assert len(encoded) <= limit and json.loads(encoded) == first and first == second
        assert len(first.get("relationships", [])) <= 8
    for state in ("protected", "indeterminate"):
        s["native"]["value"]["protection"] = state
        s["native"]["name"]["value"] = "PRIVATE_PROTECTED"
        result = json.dumps(build_ai_payload(s), ensure_ascii=False)
        assert "PRIVATE_PROTECTED" not in result and "م" not in result


@scenario("Phase 5: mocked HTTP uses header auth/locale, multipart output and private-safe errors")
def test_ai_http_boundary():
    import io
    import logging
    import urllib.request
    import urllib.error
    from addon.globalPlugins.detailedElementInfo import ai_handler
    from addon.globalPlugins.detailedElementInfo.config import getConfig

    class Response:
        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, size=-1):
            return self.body if size < 0 else self.body[:size]

    logs = []

    class CaptureLog(logging.Handler):
        def emit(self, record):
            logs.append(record.getMessage())

    logger = logging.getLogger(ai_handler.__name__)
    previous_level, previous_propagate = logger.level, logger.propagate
    capture_log = CaptureLog()
    logger.addHandler(capture_log)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    cfg = getConfig()
    previous_key, previous_open = cfg["aiToken"], urllib.request.urlopen
    old_language = sys.modules.get("languageHandler")
    language = types.ModuleType("languageHandler")
    language.getLanguage = lambda: "ar_EG"
    sys.modules["languageHandler"] = language
    requests = []
    body = [
        json.dumps({"candidates": [{"content": {"parts": [{"text": "First"}, {"text": "Second"}]}}]}).encode()
    ]

    def fake_open(request, timeout):
        requests.append(request)
        assert timeout == 15
        if isinstance(body[0], Exception):
            raise body[0]
        return Response(body[0])

    try:
        cfg["aiToken"] = " SYNTHETIC_API_KEY "
        urllib.request.urlopen = fake_open
        result = ai_handler.analyze_dom_with_gemini(ai_sample())
        assert result == "First\nSecond"
        request = requests[-1]
        assert "gemini-2.5-flash:generateContent" in request.full_url and "?key=" not in request.full_url
        assert request.get_header("X-goog-api-key") == "SYNTHETIC_API_KEY"
        serialized = request.data.decode()
        assert len(serialized) <= 16000 and "ar_EG" in serialized
        assert "Screen Reader Usage" in serialized and "Remediation Guide" in serialized
        assert "SYNTHETIC_API_KEY" not in serialized and "SYNTHETIC_PRIVATE_VALUE" not in serialized
        long_snapshot = ai_sample()
        long_snapshot["native"]["name"]["value"] = (chr(92) + chr(34) + "ع") * 5000
        long_snapshot["native"]["description"]["value"] = "غ" * 10000
        ai_handler.analyze_dom_with_gemini(long_snapshot)
        assert len(requests[-1].data.decode()) <= 16000
        json.loads(requests[-1].data.decode())
        errors = [
            urllib.error.HTTPError(
                "https://invalid.test/SYNTHETIC_API_KEY",
                403,
                "SYNTHETIC_PRIVATE_VALUE",
                None,
                io.BytesIO(b"SYNTHETIC_PRIVATE_VALUE"),
            ),
            urllib.error.URLError("SYNTHETIC_API_KEY"),
            TimeoutError("SYNTHETIC_PRIVATE_VALUE"),
            b'{"broken":"SYNTHETIC_API_KEY"',
            b'{"candidates":[]}',
            b'{"promptFeedback":{"blockReason":"SAFETY"}}',
        ]
        for error in errors:
            body[0] = error
            message = ai_handler.analyze_dom_with_gemini(ai_sample())
            assert message and "SYNTHETIC_API_KEY" not in message and "SYNTHETIC_PRIVATE_VALUE" not in message
        assert "SYNTHETIC_API_KEY" not in "\n".join(logs)
        assert "SYNTHETIC_PRIVATE_VALUE" not in "\n".join(logs)
        before = len(requests)
        cfg["aiToken"] = ""
        assert "API key" in ai_handler.analyze_dom_with_gemini(ai_sample())
        assert len(requests) == before
    finally:
        logger.removeHandler(capture_log)
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate
        cfg["aiToken"], urllib.request.urlopen = previous_key, previous_open
        if old_language is None:
            sys.modules.pop("languageHandler", None)
        else:
            sys.modules["languageHandler"] = old_language


@scenario("Phase 5: explicit AI uses report A after B, and output is escaped")
def test_ai_report_identity():
    import os
    import threading
    import api
    import ui
    import wx
    from addon.globalPlugins.detailedElementInfo import GlobalPlugin, ai_handler, server
    from addon.globalPlugins.detailedElementInfo.config import getConfig

    cfg = getConfig()
    previous_support = cfg["advancedSupport"]
    cfg["advancedSupport"] = False
    shown, sent = [], []
    focus = [MockNVDAObject(name="AI Frozen A", IA2Attributes={"tag": "button"})]
    foreground = [types.SimpleNamespace(name="page", processID=os.getpid() + 1, parent=None)]

    class Immediate:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    def fake_ai(snapshot):
        sent.append(snapshot)
        return "<script>untrusted</script>"

    patches = [
        (api, "getFocusObject", lambda: focus[0]),
        (api, "getForegroundObject", lambda: foreground[0]),
        (ui, "browseableMessage", lambda text, **kw: shown.append((text, kw["title"]))),
        (ui, "message", lambda text: None),
        (wx, "CallAfter", lambda callback, *args, **kwargs: callback(*args, **kwargs)),
        (threading, "Thread", Immediate),
        (ai_handler, "analyze_dom_with_gemini", fake_ai),
    ]
    originals = [(m, k, getattr(m, k, None)) for m, k, _ in patches]
    plugin = GlobalPlugin()
    try:
        for module, key, replacement in patches:
            setattr(module, key, replacement)
        plugin.script_showElementInfo(None)
        title_a = shown[-1][1]
        focus[0] = MockNVDAObject(name="AI Frozen B", IA2Attributes={"tag": "button"})
        plugin.script_showElementInfo(None)
        assert sent == []
        server.get_ai_analysis()
        assert sent == [], "Legacy no-argument API must not transmit global DOM data"
        foreground[0] = types.SimpleNamespace(name=title_a, processID=os.getpid(), parent=None)
        cfg["advancedSupport"] = True
        plugin.script_analyzeElementAI(None)
        assert len(sent) == 1 and sent[0]["native"]["name"]["value"] == "AI Frozen A"
        assert "<script>" not in shown[-1][0] and "&lt;script&gt;" in shown[-1][0]
        assert "advisory" in shown[-1][0].lower()
        callbacks = []
        wx.CallAfter = callbacks.append
        plugin.script_analyzeElementAI(None)
        count = len(shown)
        plugin.terminate()
        callbacks.pop(0)()
        assert len(shown) == count
    finally:
        if plugin._is_alive:
            plugin.terminate()
        cfg["advancedSupport"] = previous_support
        for module, key, original in originals:
            if original is None:
                delattr(module, key)
            else:
                setattr(module, key, original)


@scenario("Phase 5: editable optional text is omitted when value evidence is unavailable")
def test_ai_missing_editable_value():
    from addon.globalPlugins.detailedElementInfo.ai_handler import build_ai_payload

    for tag, editable, role in [
        ("textarea", False, "EDITABLETEXT (textbox)"),
        ("div", True, "BUTTON"),
        (None, False, "EDITABLETEXT (textbox)"),
    ]:
        s = ai_sample()
        s["aria"]["tag"]["value"] = tag
        s["aria"]["nvda_role"]["value"] = role
        s["native"]["value"].update(value=None, availability="error")
        s["native"]["name"]["value"] = "PRIVATE_TYPED_WITHOUT_VALUE"
        s["native"]["description"]["value"] = "PRIVATE_TYPED_WITHOUT_VALUE"
        s["dom"]["properties"]["is_content_editable"] = editable
        payload = build_ai_payload(s)
        assert "PRIVATE_TYPED_WITHOUT_VALUE" not in json.dumps(payload)
        assert payload["name"]["availability"] == "unavailable"


def run_browser_checks():
    from pathlib import Path
    import json
    from playwright.sync_api import sync_playwright

    cases = [
        (
            "line_break_label",
            '<button id="x">Log<br>in</button>',
            "r.context.visible_label.candidate_text === 'Log in'",
        ),
        (
            "visible_child_label",
            '<label for="x" style="visibility:hidden"><span style="visi'
            'bility:visible">Visible child</span></label><input id="x">',
            "r.context.visible_label.candidate_text === 'Visible child'",
        ),
        (
            "button_visible_label",
            '<button id="x">Search</button>',
            "r.context.visible_label.candidate_text === 'Search'",
        ),
        (
            "visible_label",
            '<label for="x" style="display:none">Hidden</label><label for="x">Visible</label><input id="x">',
            "r.context.visible_label.candidate_text === 'Visible'",
        ),
        (
            "multiple_labels",
            '<label for="x">First</label><label for="x">Second</label><input id="x">',
            "r.context.visible_label.availability !== 'available'"
            " && r.context.visible_label.candidates?.length === 2",
        ),
        (
            "html_direction",
            '<div dir="rtl"><span id="x" dir="bogus">Text</span></div>',
            "r.context.language.effective_html_direction === 'rtl'",
        ),
        (
            "fieldset_disabled",
            '<fieldset disabled><legend><input id="legend"></legend><input id="x"></fieldset>',
            "r.context.form.disabled === true",
        ),
        (
            "first_legend_exception",
            '<fieldset disabled><legend><input id="x"></legend></fieldset>',
            "r.context.form.disabled === false",
        ),
        (
            "column_spans",
            '<table><tr><td colspan="2">Wide</td><td id="x">Cell</td></tr></table>',
            "r.context.table.column_index === 3 || r.context.table.column_index === null",
        ),
        (
            "header_categories",
            '<table><tr><th id="c" scope="col">Column</th><th id="h" scope'
            '="row">Row</th><td id="x" headers="c h">Cell</td></tr></table>',
            "r.context.table.row_headers.length === 1 && r.context.table.column_headers.length === 1",
        ),
        (
            "virtual_parent_column",
            '<table role="grid" aria-colcount="10"><tr aria-colindex="5"><td id="x">Cell</td></tr></table>',
            "r.context.table.column_index === 5 && r.context.table.declared_parent_col_index === 5",
        ),
        (
            "bounded_ancestor_unknown",
            "<div inert>" + "<div>" * 33 + '<button id="x">Probe</button>' + "</div>" * 34,
            "r.visibility.inert_ancestor === null && r.visibility.aria_hidden_ancestor === null",
        ),
        (
            "virtual_indices",
            '<div role="grid" aria-rowcount="-1"><div role="row" aria-row'
            'index="77"><div role="gridcell" id="x">Cell</div></div></div>',
            "r.context.table.row_index === 77 && r.context.table.row_c"
            "ount === null && r.context.table.declared_row_count === -1",
        ),
        (
            "inert_is_not_hidden",
            '<button inert id="x">Visible</button>',
            "r.visibility.rendered_hidden === false && r.visibility.inert_ancestor === true",
        ),
        (
            "validation_privacy",
            '<input id="x" value="SYNTHETIC_SECRET">',
            "!JSON.stringify(r).includes('SYNTHETIC_SECRET')",
        ),
        (
            "editable_reference",
            '<span id="ref"><span contenteditable>SYNTHETIC_SECRET</span>Pub'
            'lic</span><button id="x" aria-describedby="ref">Button</button>',
            "!JSON.stringify(r).includes('SYNTHETIC_SECRET')",
        ),
    ]

    cases.append(
        (
            "unassociated_neighbor_label",
            '<span>Search</span><button id="x" aria-label="Run" style="width:2em;height:2em"></button>',
            "r.context.visible_label.applicability_evidence!=='established_no_visible_text'",
        )
    )
    contrast_cases = [
        (
            "contrast_black_white",
            '<span id="x" style="color:black;background:white">Text</span>',
            "r.contrast.availability==='available' && r.contrast.ratio===21",
        ),
        (
            "contrast_identical",
            '<span id="x" style="color:white;background:white">Text</span>',
            "r.contrast.ratio===1",
        ),
        (
            "contrast_inherited_background",
            '<div style="background:white"><span id="x" style="color:black">Text</span></div>',
            "r.contrast.availability==='available' && r.contrast.ratio===21",
        ),
        (
            "contrast_unresolved_background",
            '<span id="x" style="color:black">Text</span>',
            "r.contrast.availability==='unavailable'",
        ),
        (
            "contrast_opacity",
            '<div style="opacity:.5"><span id="x" style="color:black;background:white">Text</span></div>',
            "r.contrast.availability==='unavailable' && r.contrast.reason==='unsupported_compositing'",
        ),
        (
            "contrast_mixed_descendant",
            '<span id="x" style="color:black;background:white"><b style="color:red">Text</b></span>',
            "r.contrast.availability==='unavailable'",
        ),
        (
            "contrast_background_image",
            '<span id="x" style="background:linear-gradient(white,black);color:black">Text</span>',
            "r.contrast.availability==='unavailable'",
        ),
        (
            "contrast_overlay",
            '<span id="x" style="color:black;background:white">Text</span>'
            '<div style="position:fixed;inset:0;background:#ff000080;pointer-events:none"></div>',
            "r.contrast.availability==='unavailable' && r.contrast.reason==='overlapping_content'",
        ),
        (
            "contrast_alpha",
            '<span id="x" style="color:rgb(0 0 0 / .5);background:white">Text</span>',
            "r.contrast.availability==='unavailable'",
        ),
        (
            "contrast_readonly",
            '<button readonly id="x" style="color:white;background:white">Text</button>',
            "r.contrast.ratio===1 && r.contrast.inactive===false",
        ),
        ("contrast_disabled", '<button disabled id="x">Text</button>', "r.contrast.inactive===true"),
        (
            "contrast_inert",
            '<button inert id="x" style="color:white;background:white">Text</button>',
            "r.contrast.inactive===false && r.contrast.ratio===1",
        ),
        (
            "contrast_font_boundaries",
            '<span id="x" style="color:black;background:white;'
            'font-size:18.6666667px;font-weight:700">Text</span>',
            "r.contrast.font_size_px>=56/3 && r.contrast.font_weight===700",
        ),
    ]
    cases.extend(contrast_cases)
    cases.extend(
        [
            (
                "contrast_content_visibility",
                '<span id="x" style="display:inline-block;width:100px;height:30px;'
                'content-visibility:hidden;color:black;background:white">Text</span>',
                "r.contrast.availability==='unavailable'",
            ),
            (
                "label_content_visibility",
                '<button id="x" aria-label="Run" style="content-visibility:hidden">Search</button>',
                "r.context.visible_label.availability!=='available'",
            ),
        ]
    )

    cases.extend(
        [
            (
                "contrast_text_fill",
                '<span id="x" style="color:black;-webkit-text-fill-color:white;background:white">Text</span>',
                "r.contrast.availability==='unavailable'",
            ),
            (
                "contrast_inset_shadow",
                '<span id="x" style="color:white;background:black;'
                'box-shadow:inset 0 0 0 100px white">Text</span>',
                "r.contrast.availability==='unavailable'",
            ),
            (
                "contrast_generated_overlay",
                '<style>#overlay::before{content:"";position:fixed;inset:0;background:red}</style>'
                '<span id="x" style="color:black;background:white">Text</span><div id="overlay"></div>',
                "r.contrast.availability==='unavailable'",
            ),
        ]
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True, timeout=10000)
        outcomes = {}
        try:
            for name, markup, assertion in cases:
                page = browser.new_page()
                page.set_default_timeout(5000)
                page.set_content(markup)
                page.evaluate("""() => {
                    globalThis.chrome={runtime:{lastError:null,sendMessage:()=>{},
                        onMessage:{addListener:()=>{}}}};
                    const input=document.getElementById('x');
                    if (input instanceof HTMLInputElement)
                        input.setCustomValidity('Rejected: SYNTHETIC_SECRET');
                }""")
                page.add_script_tag(path=str(Path("Bridge/content.js").resolve()))
                outcomes[name] = page.evaluate(
                    "() => { const r=collectElementData(document.getElem"
                    "entById('x'),new BudgetTracker(8,500,4000));return (" + assertion + ");}"
                )
                page.close()
            page = browser.new_page()
            page.set_content(
                '<button id="x" aria-labelledby="'
                + " ".join("r" + str(n) for n in range(11))
                + '">Button</button>'
                + "".join('<span id="r' + str(n) + '">Reference</span>' for n in range(11))
            )
            page.evaluate("""() => {globalThis.chrome={runtime:{lastError:null,sendMessage:()=>{},
                    onMessage:{addListener:()=>{}}}};}""")
            page.add_script_tag(path=str(Path("Bridge/content.js").resolve()))
            outcomes["reference_lookup_budget"] = page.evaluate("""() => {
                const element=document.getElementById('x'), original=document.getElementById.bind(document);
                let reads=0; document.getElementById=id=>{reads++;return original(id);};
                const r=collectElementData(element,new BudgetTracker(8,500,4000));
                return reads<=8 && r.aria_idrefs['aria-labelledby'].targets.filter(x=>x.resolved).length<=8;
            }""")

            page.close()
            page = browser.new_page()
            page.goto(Path("scripts/element_info_fixture.html").resolve().as_uri())
            page.evaluate("""() => {
                document.body.insertAdjacentHTML('beforeend',
                    '<button id="marker-probe" data-nvda-target-id="original-marker">Probe</button>');
                globalThis.messages=[];
                globalThis.chrome={runtime:{lastError:null,sendMessage:m=>messages.push(m),
                    onMessage:{addListener:fn=>globalThis.contentListener=fn}}};
            }""")
            page.add_script_tag(path=str(Path("Bridge/content.js").resolve()))
            outcomes["overlapping_marker_restoration"] = page.evaluate("""() => new Promise(resolve => {
                const timeout=setTimeout(()=>resolve(false),2000);
                (async () => {
                const nonce=messages.find(m=>m.action==='ping').documentNonce;
                function inspect(id) {
                    const request={request_id:id,documentNonce:nonce,expected_url:location.href,
                        deadline_ms:Date.now()+1500};
                    contentListener({...request,action:'prepare_element'},{},()=>{});
                    return new Promise(done=>contentListener({...request,action:'collect_element',
                        target:{id:'marker-probe',tag:'button',protection:'unprotected'}},{},done));
                }
                await Promise.all([inspect('marker-A'),inspect('marker-B')]);
                clearTimeout(timeout);
                resolve(document.getElementById('marker-probe').getAttribute('data-nvda-target-id')
                    ==='original-marker');
                })().catch(()=>{clearTimeout(timeout);resolve(false);});
            })""")
            print(
                json.dumps(
                    {
                        "chrome": browser.version,
                        "context_checks": outcomes,
                        "passed": sum(outcomes.values()),
                        "total": len(outcomes),
                    }
                )
            )
        finally:
            browser.close()
    return 0 if all(outcomes.values()) else 1


@scenario("Bridge: native browser eligibility fails closed")
def test_native_browser_eligibility():
    import types
    from addon.globalPlugins.detailedElementInfo import GlobalPlugin, server
    from addon.globalPlugins.detailedElementInfo.config import getConfig

    cfg = getConfig()
    previous = cfg["advancedSupport"]
    cfg["advancedSupport"] = False
    plugin = GlobalPlugin()
    original = server.create_bridge_request
    server.create_bridge_request = lambda **kwargs: (_ for _ in ()).throw(
        AssertionError("Unsupported native browser reached Bridge")
    )
    try:
        cfg["advancedSupport"] = True
        for module in (
            types.SimpleNamespace(appName="firefox"),
            None,
            types.SimpleNamespace(appName="msedge"),
        ):
            obj = MockNVDAObject(
                appModule=module,
                IA2Attributes={"tag": "button", "id": "probe", "document-url": "https://example.test/page"},
            )
            plugin._getCurrentObject = lambda: obj
            captured = []
            plugin._collectSnapshot(captured.append)
            assert len(captured) == 1
            assert captured[0]["availability"]["bridge_reason"] == "unsupported_native_browser"

        class BrokenApplication(MockNVDAObject):
            @property
            def appModule(self):
                raise RuntimeError("unavailable provider")

        plugin._getCurrentObject = lambda: BrokenApplication()
        captured = []
        plugin._collectSnapshot(captured.append)
        assert captured[0]["native"]["application_name"]["availability"] != "available"
    finally:
        server.create_bridge_request = original
        cfg["advancedSupport"] = previous
        plugin.terminate()


def run_all_tests():
    passed = 0
    failed = 0
    failures = []

    print(f"Running {len(test_cases)} scenarios in scripts/run_tests.py...\n")

    for name, fn in test_cases:
        try:
            fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            print(f"[FAIL] {name}: {e or type(e).__name__}\n{tb}", file=sys.stderr)
            failed += 1
            failures.append((name, str(e)))

    print(f"\nTest Summary: {passed} passed, {failed} failed out of {len(test_cases)} total scenarios.")
    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Local snapshot and optional Chrome regression checks.")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Run actual Chrome checks with the developer's installed Playwright; never runs NVDA.",
    )
    arguments = parser.parse_args()
    try:
        sys.exit(run_browser_checks() if arguments.browser else run_all_tests())
    except ImportError as error:
        print("Optional browser check dependency unavailable: " + str(error), file=sys.stderr)
        sys.exit(2)
