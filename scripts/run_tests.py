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
                def __init__(self): pass
                def terminate(self): pass
            m.GlobalPlugin = GlobalPlugin
        elif mod_name == "scriptHandler":
            m.script = lambda **kwargs: (lambda fn: fn)
        elif mod_name == "gui":
            class SettingsPanel:
                def __init__(self, *args, **kwargs): pass
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
            self.positionInfo = kwargs.get("positionInfo", {"indexInGroup": 1, "similarItemsInGroup": 3, "level": 1})
        self.location = kwargs.get("location", (10, 20, 100, 30))
        self.parent = kwargs.get("parent", None)
        if "IA2Attributes" not in self.__class__.__dict__:
            self.IA2Attributes = kwargs.get("IA2Attributes", {"tag": "input", "id": "test-input", "type": "text"})
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
    assert secret_pass not in json.dumps(snap1), "Sensitive password leaked anywhere into serialized snapshot!"
    
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
        positionInfo={"indexInGroup": 2, "similarItemsInGroup": 5}
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
        "object", "rawAttrs", "derivedAttrs", "tag", "domPath",
        "accessibleName", "nameSource", "nameConfidence", "explicitRole",
        "nativeRole", "nvdaRole", "finalRole", "semanticSource",
        "nativeSemanticMismatch", "headingLevel", "msaaRole"
    ]
    for key in required_legacy_keys:
        assert key in data, f"Legacy key '{key}' missing from analyzer.analyze result"
        
    # Also provides the snapshot
    assert "snapshot" in data, "analyzer.analyze must include 'snapshot' key"
    
    # ReportBuilder._formatElement and buildReport work with data
    builder = ReportBuilder(analyzer)
    html_report = builder.buildReport(obj)
    assert "<h1>Detailed Element Info</h1>" in html_report
    assert "<h2>Current element</h2>" in html_report


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
        role=1,  # EDITABLETEXT
        roleString="edit",
        IA2Attributes={"tag": "div", "xml-roles": "button"}
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

    assert not bare._value_read_attempted, "Private value getter was accessed during indeterminate protection!"
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
        isProtected=True,
        IA2Attributes={"tag": "input", "type": "password", "value": sentinel, "name": "pwd"}
    )
    snap = analyzer.build_snapshot(obj)
    data = analyzer.analyze(obj)
    html = builder.buildReport(obj)

    assert sentinel not in json.dumps(snap), "Sentinel password leaked into serialized snapshot!"
    assert sentinel not in html, "Sentinel password leaked into HTML report!"
    assert sentinel not in str(data["rawAttrs"]), "Sentinel password leaked into legacy rawAttrs!"
    assert data["rawAttrs"].get("type") == "password", "Unrelated attribute type='password' must be preserved!"


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

    assert target_name == native_name == legacy_name, (
        f"Name re-collected multiple times: target={target_name}, native={native_name}, legacy={legacy_name}"
    )


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
        }
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


@scenario("Regression 10: Snapshot module is compatible with Python 3.7 runtime (no PEP 604/PEP 585 runtime expressions)")
def test_snapshot_python37_compatibility():
    import ast
    import inspect
    from addon.globalPlugins.detailedElementInfo import snapshot

    # 1. ObservationValue must not be a Python 3.10+ types.UnionType
    union_type = getattr(types, "UnionType", None)
    if union_type is not None:
        assert not isinstance(snapshot.ObservationValue, union_type), (
            "ObservationValue must use typing.Union/Optional for Python 3.7 compatibility, not PEP 604 '|'"
        )

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
                    f"PEP 585 subscript on builtin '{node.value.id}' found at line {node.lineno}; incompatible with Python 3.7 runtime"
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
        protected = analyzer.analyze(MockNVDAObject(
            IA2Attributes={"tag": tag}, value=url, isProtected=True))
        assert key not in protected["rawAttrs"]
    existing = analyzer.analyze(MockNVDAObject(
        IA2Attributes={"tag": "a", "href": "original"}, value=url))
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
            print(f"[FAIL] {name}: {e}")
            failed += 1
            failures.append((name, str(e)))
            
    print(f"\nTest Summary: {passed} passed, {failed} failed out of {len(test_cases)} total scenarios.")
    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
