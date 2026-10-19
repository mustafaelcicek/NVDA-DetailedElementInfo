import itertools
from typing import Any, Dict, Optional
import uuid
import controlTypes

try:
    import logHandler

    log = logHandler.log
except Exception:
    log = None

from .roleMaps import (
    STATE_TO_ARIA,
    NVDA_ROLE_TO_ARIA,
    getNativeAriaRole,
    getHeadingLevel,
)
from .snapshot import (
    SOURCE_NVDA,
    SOURCE_IA2_ATTR,
    SOURCE_IA2_REL,
    SOURCE_DOM,
    SOURCE_DERIVED,
    AVAIL_AVAILABLE,
    AVAIL_UNAVAILABLE,
    AVAIL_UNSUPPORTED,
    AVAIL_ERROR,
    PROTECTION_PROTECTED,
    PROTECTION_UNPROTECTED,
    PROTECTION_INDETERMINATE,
    create_observation,
    create_empty_snapshot,
)


class ElementAnalyzer:
    def analyze(self, obj):
        snapshot = self.build_snapshot(obj)

        rawAttrs = dict(snapshot["aria"]["raw_attributes"])
        derivedAttrs = dict(snapshot["aria"]["derived_attributes"])

        tag = snapshot["aria"]["tag"]["value"] or ""
        captured_value = snapshot["native"]["value"]
        if captured_value["availability"] == AVAIL_AVAILABLE and captured_value["value"]:
            if tag == "a":
                rawAttrs.setdefault("href", captured_value["value"])
            elif tag == "#document":
                rawAttrs["document-url"] = captured_value["value"]
        domPath = self.buildDomPath(obj, initialAttrs=rawAttrs)

        accessibleName = snapshot["native"]["name"]["value"]
        nameSource, nameConfidence = self.getNameSource(None, rawAttrs, name=accessibleName)

        explicitRole = snapshot["aria"]["explicit_role"]["value"]
        nativeRole = snapshot["aria"]["native_role"]["value"]
        nvdaRole = snapshot["aria"]["nvda_role"]["value"]
        finalRole = snapshot["aria"]["final_role"]["value"]

        semanticSource = self.getSemanticSource(explicitRole, nativeRole, tag)
        nativeSemanticMismatch = self.getNativeSemanticMismatch(
            explicitRole,
            nativeRole,
            tag,
        )

        headingLevel = getHeadingLevel(tag, rawAttrs)
        msaaRole = snapshot["native"]["msaa_role"]["value"]

        for key, value in {
            "dom_path": domPath,
            "name_source": nameSource,
            "name_confidence": nameConfidence,
            "semantic_source": semanticSource,
            "semantic_mismatch": nativeSemanticMismatch,
            "heading_level": headingLevel,
        }.items():
            snapshot["native"][key] = create_observation(
                value, SOURCE_DERIVED, AVAIL_AVAILABLE if value is not None else AVAIL_UNAVAILABLE
            )
        return {
            "object": obj,
            "rawAttrs": rawAttrs,
            "derivedAttrs": derivedAttrs,
            "tag": tag,
            "domPath": domPath,
            "accessibleName": accessibleName,
            "nameSource": nameSource,
            "nameConfidence": nameConfidence,
            "explicitRole": explicitRole,
            "nativeRole": nativeRole,
            "nvdaRole": nvdaRole,
            "finalRole": finalRole,
            "semanticSource": semanticSource,
            "nativeSemanticMismatch": nativeSemanticMismatch,
            "headingLevel": headingLevel,
            "msaaRole": msaaRole,
            "snapshot": snapshot,
        }

    def build_snapshot(self, obj, request_id=None):
        """
        Build a frozen, serializable snapshot of the captured NVDA target.
        Conforms to the Phase 0 plain-dictionary schema and Phase 1 native expansion.
        All root properties are captured once from the provider object and reused.
        """
        req_id = str(request_id) if request_id is not None else str(uuid.uuid4())
        snapshot = create_empty_snapshot(req_id)

        # Single guarded capture of root properties
        name_val, name_avail = self._safe_read(obj, "name")
        role_val, role_avail = self._safe_read(obj, "role")
        role_str_val, role_str_avail = self._safe_read(obj, "roleString")
        desc_val, desc_avail = self._safe_read(obj, "description")
        sc_val, sc_avail = self._safe_read(obj, "keyboardShortcut")
        loc_val, loc_avail = self._safe_read(obj, "location")
        wh_val, wh_avail = self._safe_read(obj, "windowHandle")
        app_module, app_avail = self._safe_read(obj, "appModule")
        app_name, app_name_avail = (
            self._safe_read(app_module, "appName") if app_module is not None else (None, app_avail)
        )
        pos_val, pos_avail = self._safe_read(obj, "positionInfo")

        states_val = None
        states_list = []
        try:
            states_val = getattr(obj, "states", None)
            if states_val is not None:
                states_list = [getattr(s, "name", str(s)) for s in states_val]
                states_avail = AVAIL_AVAILABLE
            else:
                states_avail = AVAIL_UNAVAILABLE
        except NotImplementedError:
            states_avail = AVAIL_UNSUPPORTED
        except Exception:
            states_avail = AVAIL_ERROR

        try:
            is_prot_val = getattr(obj, "isProtected", None)
            if is_prot_val is None:
                is_prot_avail = AVAIL_UNAVAILABLE
            else:
                is_prot_avail = AVAIL_AVAILABLE
        except NotImplementedError:
            is_prot_val = None
            is_prot_avail = AVAIL_UNSUPPORTED
        except Exception:
            is_prot_val = None
            is_prot_avail = AVAIL_ERROR

        raw_attrs = {}
        try:
            ia2_val = getattr(obj, "IA2Attributes", None)
            if ia2_val is not None:
                raw_attrs = dict(ia2_val)
                ia2_avail = AVAIL_AVAILABLE if bool(raw_attrs) else AVAIL_UNAVAILABLE
            else:
                ia2_avail = AVAIL_UNAVAILABLE
        except NotImplementedError:
            ia2_avail = AVAIL_UNSUPPORTED
        except Exception:
            ia2_avail = AVAIL_ERROR

        snapshot["availability"]["ia2"] = ia2_avail

        # Protection evaluation (tri-state, fails closed)
        protection = self._evaluate_protection(
            is_prot_val, is_prot_avail, states_val, states_avail, role_val, raw_attrs
        )

        # Sanitize raw_attrs: strip private value if protected or indeterminate
        if protection != PROTECTION_UNPROTECTED:
            raw_attrs.pop("value", None)

        # Guarded value read: only read obj.value when positive non-protection is established!
        if protection == PROTECTION_UNPROTECTED:
            val, val_avail = self._safe_read(obj, "value")
            val_obs = create_observation(
                val,
                SOURCE_NVDA,
                val_avail,
                protection=PROTECTION_UNPROTECTED,
                protected=False,
            )
        elif protection == PROTECTION_PROTECTED:
            val_obs = create_observation(
                None,
                SOURCE_NVDA,
                AVAIL_UNAVAILABLE,
                protection=PROTECTION_PROTECTED,
                protected=True,
            )
        else:
            val_obs = create_observation(
                None,
                SOURCE_NVDA,
                AVAIL_UNAVAILABLE,
                protection=PROTECTION_INDETERMINATE,
            )

        # Target Identity
        snapshot["target"]["target_identity"] = {
            "name": name_val,
            "role": role_val,
            "role_name": role_str_val,
            "states": states_list,
            "window_handle": wh_val,
        }

        # Native Section
        msaa_role = self.getMsaaRole(obj)
        snapshot["native"] = {
            "name": create_observation(name_val, SOURCE_NVDA, name_avail),
            "role": create_observation(role_val, SOURCE_NVDA, role_avail),
            "role_text": create_observation(role_str_val, SOURCE_NVDA, role_str_avail),
            "description": create_observation(desc_val, SOURCE_NVDA, desc_avail),
            "keyboard_shortcut": create_observation(sc_val, SOURCE_NVDA, sc_avail),
            "application_name": create_observation(app_name, SOURCE_NVDA, app_name_avail),
            "value": val_obs,
            "position_info": create_observation(pos_val, SOURCE_NVDA, pos_avail),
            "states": create_observation(states_list, SOURCE_NVDA, states_avail),
            "location": create_observation(loc_val, SOURCE_NVDA, loc_avail),
            "msaa_role": create_observation(
                msaa_role,
                SOURCE_NVDA,
                AVAIL_AVAILABLE if msaa_role is not None else AVAIL_UNAVAILABLE,
            ),
        }

        # Derived attributes from captured states
        derived_attrs = {}
        if states_avail == AVAIL_AVAILABLE and states_val is not None:
            for stateName, ariaAttr, ariaValue in STATE_TO_ARIA:
                try:
                    state = getattr(controlTypes.State, stateName, None)
                    if state is not None and state in states_val:
                        if ariaAttr not in derived_attrs:
                            derived_attrs[ariaAttr] = ariaValue
                except Exception:
                    pass

        # Roles for ARIA section
        tag = raw_attrs.get("tag", "").strip().lower()
        explicitRole = self.getExplicitRole(raw_attrs)
        nativeRole = getNativeAriaRole(raw_attrs, tag)
        nvdaRole = self._computeNvdaRoleString(role_val)
        finalRole = self.getFinalRole(explicitRole, nativeRole, nvdaRole)

        reference_budget = {"targets_remaining": 8, "characters_remaining": 4000, "truncated": False}
        snapshot["availability"]["reference_budget"] = reference_budget
        # ARIA Section
        snapshot["aria"] = self._build_aria_section(
            obj,
            raw_attrs,
            derived_attrs,
            tag,
            explicitRole,
            nativeRole,
            nvdaRole,
            finalRole,
            reference_budget,
        )

        # Context Section
        snapshot["context"] = self._build_context_section(
            obj, raw_attrs, states_val, states_avail, pos_val, pos_avail, reference_budget
        )

        return snapshot

    def build_target_info(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build target criteria dictionary for Bridge matching from captured snapshot evidence.
        Never re-reads live NVDA target properties.
        """
        target_id = snapshot.get("target", {}).get("target_identity", {})
        aria = snapshot.get("aria", {})
        native = snapshot.get("native", {})
        location_obs = native.get("location", {})
        loc_val = location_obs.get("value")

        target_info: Dict[str, Any] = {
            "name": target_id.get("name") or "",
            "role": target_id.get("role_name") or "",
            "role_value": target_id.get("role") if target_id.get("role") is not None else -1,
            "tag": aria.get("tag", {}).get("value") or "",
            "id": aria.get("id", {}).get("value") or "",
            "class": aria.get("class_name", {}).get("value") or "",
            "nvda_selector": self.domPathSegment(aria.get("raw_attributes", {})),
            "protection": native.get("value", {}).get("protection", PROTECTION_INDETERMINATE),
            "reference_budget": dict(snapshot.get("availability", {}).get("reference_budget", {})),
        }

        if isinstance(loc_val, (list, tuple)) and len(loc_val) >= 4:
            target_info["width"] = loc_val[2]
            target_info["height"] = loc_val[3]

        return target_info

    def get_expected_document_url(self, obj: Any, snapshot: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Capture reliable expected document URL using captured snapshot evidence
        or bounded ancestor traversal (up to 32) on the NVDA UI thread.
        """
        if snapshot is not None:
            doc_id = snapshot.get("target", {}).get("document_identity")
            if isinstance(doc_id, dict) and doc_id.get("url"):
                return str(doc_id["url"])
            raw_attrs = snapshot.get("aria", {}).get("raw_attributes", {})
            if "document-url" in raw_attrs and raw_attrs["document-url"]:
                return str(raw_attrs["document-url"])
            tag = raw_attrs.get("tag", "").strip().lower()
            if tag == "#document":
                val_obs = snapshot.get("native", {}).get("value", {})
                if val_obs.get("availability") == AVAIL_AVAILABLE and val_obs.get("value"):
                    return str(val_obs["value"])

        if obj is None:
            return None

        try:
            current = getattr(obj, "parent", None)
            depth = 0
            while current is not None and depth < 32:
                depth += 1
                try:
                    attrs = self.getRawAttrs(current)
                except Exception:
                    attrs = {}

                tag = attrs.get("tag", "").strip().lower()
                if tag == "#document":
                    doc_url = attrs.get("document-url")
                    if doc_url:
                        return str(doc_url)
                    if not self._check_is_protected(current):
                        try:
                            val = getattr(current, "value", None)
                            if val:
                                return str(val)
                        except Exception:
                            pass
                    break

                try:
                    current = current.parent
                except Exception:
                    break
        except Exception:
            pass

        return None

    def enrich_snapshot_with_dom(self, snapshot: Dict[str, Any], dom_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich captured snapshot with verified Chrome Bridge response data.
        Freezes DOM, layout, ARIA IDREFs, and 5 context groups.
        """
        if not isinstance(dom_data, dict):
            return snapshot

        if dom_data.get("error"):
            snapshot["availability"]["bridge"] = AVAIL_ERROR
            return snapshot

        snapshot["availability"]["bridge"] = AVAIL_AVAILABLE

        import copy

        # Deepcopy to prevent mutating original caller data
        dom_data = copy.deepcopy(dom_data)

        # Fail-closed protection check
        val_obs = snapshot.get("native", {}).get("value", {})
        protection = val_obs.get("protection")
        is_protected = (
            protection is None or protection != PROTECTION_UNPROTECTED or val_obs.get("protected") is True
        )

        if is_protected:
            # Never parse private markup to guess which portions contain a value.
            dom_data["value"] = None
            dom_data["attributes"] = {}
            dom_data["innerText"] = None
            dom_data["outerHTML"] = None
            dom_data["aria_idrefs"] = {}
            dom_data["frameworkEvents"] = {}
            dom_data["context"] = {}

        # 1. Target Identities
        doc_nonce = dom_data.get("documentNonce")
        snapshot["target"]["element_identity"] = {
            "tag": dom_data.get("tag"),
            "id": dom_data.get("id"),
            "class_name": dom_data.get("className"),
            "nonce": doc_nonce,
        }
        snapshot["target"]["document_identity"] = {
            "url": dom_data.get("document_url"),
            "title": dom_data.get("document_title"),
            "nonce": doc_nonce,
        }
        snapshot["target"]["frame_identity"] = {
            "frame_id": dom_data.get("frame_id"),
            "is_top_frame": dom_data.get("is_top_frame"),
            "supported": dom_data.get("frame_supported"),
        }

        # 2. DOM Section
        snapshot["dom"]["availability"] = AVAIL_AVAILABLE
        snapshot["dom"]["attributes"] = dom_data.get("attributes", {})
        snapshot["dom"]["properties"] = {
            "tab_index": dom_data.get("tabIndex"),
            "is_content_editable": dom_data.get("isContentEditable"),
            "disabled": dom_data.get("disabled"),
            "hidden": dom_data.get("hidden"),
            "inert": dom_data.get("inert"),
            "is_connected": dom_data.get("isConnected"),
            "tag_name": dom_data.get("tag"),
            "inner_text_excerpt": dom_data.get("innerText"),
            "value": dom_data.get("value"),
            "safe_outer_html": dom_data.get("outerHTML"),
            "inline_events": dom_data.get("inlineEvents", {}),
            "framework_events": dom_data.get("frameworkEvents", {}),
        }
        snapshot["dom"]["aria_idrefs"] = dom_data.get("aria_idrefs", {})

        # 3. Layout Section
        snapshot["layout"]["availability"] = AVAIL_AVAILABLE
        snapshot["layout"]["bounds"] = dom_data.get("bounds")
        snapshot["layout"]["viewport_intersection"] = dom_data.get("viewport_intersection")
        snapshot["layout"]["visibility"] = dom_data.get("visibility")
        snapshot["layout"]["styles"] = dom_data.get("css", {})
        snapshot["layout"]["contrast"] = dom_data.get("contrast")

        # Keep each DOM observation separate from native/IA2 evidence.
        dom_context = dom_data.get("context", {})
        if isinstance(dom_context, dict):
            label = dom_context.get("visible_label")
            if isinstance(label, dict):
                label_availability = label.get("availability", AVAIL_UNAVAILABLE)
                if label_availability not in (
                    AVAIL_AVAILABLE,
                    AVAIL_UNAVAILABLE,
                    AVAIL_ERROR,
                    AVAIL_UNSUPPORTED,
                ):
                    label_availability = AVAIL_UNAVAILABLE
                snapshot["context"]["visible_label"] = create_observation(
                    label.get("candidate_text"),
                    SOURCE_DOM,
                    label_availability,
                    source_element=label.get("source_element"),
                    applicability_evidence=label.get("applicability_evidence"),
                    candidates=label.get("candidates"),
                    truncated=label.get("truncated", False),
                )
            aliases = {
                "aria_activedescendant": "active_descendant",
                "is_selected": "selected",
                "is_focused": "focused",
                "disabled": "disabled",
            }
            for group in ("language", "form", "table", "composite"):
                values = dom_context.get(group)
                if not isinstance(values, dict):
                    continue
                destination = snapshot["context"].setdefault(group, {})
                for key, value in values.items():
                    observation = create_observation(
                        value,
                        SOURCE_DOM,
                        AVAIL_AVAILABLE if value is not None else AVAIL_UNAVAILABLE,
                    )
                    if group == "table" and key in ("row_count", "column_count") and value == -1:
                        observation = create_observation(
                            None, SOURCE_DOM, AVAIL_UNAVAILABLE, reason="unknown_total", declared_value=-1
                        )
                        destination["declared_" + key] = create_observation(-1, SOURCE_DOM, AVAIL_AVAILABLE)
                    dom_key = "dom_" + aliases.get(key, key)
                    destination[dom_key] = observation
                    original = destination.get(key)
                    if not isinstance(original, dict) or original.get("availability") != AVAIL_AVAILABLE:
                        destination[key] = observation
                if group == "composite":
                    active = values.get("aria_activedescendant")
                    destination["active_descendant"] = create_observation(
                        active,
                        SOURCE_DOM,
                        AVAIL_AVAILABLE if active is not None else AVAIL_UNAVAILABLE,
                        resolved=values.get("resolved_activedescendant"),
                    )
        usage = dom_data.get("reference_budget", {})
        remaining = snapshot["availability"].get("reference_budget")
        if isinstance(usage, dict) and isinstance(remaining, dict):
            for used_key, remaining_key in (
                ("targets_used", "targets_remaining"),
                ("characters_used", "characters_remaining"),
            ):
                used = usage.get(used_key)
                if type(used) is int and used >= 0:
                    remaining[remaining_key] = max(0, remaining[remaining_key] - used)
            remaining["truncated"] = remaining["truncated"] or usage.get("truncated") is True

        return snapshot

    def _safe_read(self, obj, prop_name):
        """
        Guarded property read from external boundary object.
        Preserves False, 0, and known empty string as available.
        Distinguishes unsupported from error and unavailable.
        """
        try:
            val = getattr(obj, prop_name, None)
        except NotImplementedError:
            return None, AVAIL_UNSUPPORTED
        except Exception:
            self._logDebug("External boundary error reading property '{}'".format(prop_name))
            return None, AVAIL_ERROR

        if val is None:
            return None, AVAIL_UNAVAILABLE
        return val, AVAIL_AVAILABLE

    def _evaluate_protection(self, is_prot_val, is_prot_avail, states_val, states_avail, role_val, raw_attrs):
        """
        Evaluate protection tri-state:
        - PROTECTION_PROTECTED: positive evidence of protection.
        - PROTECTION_UNPROTECTED: positive evidence of non-protection.
        - PROTECTION_INDETERMINATE: evidence unavailable, conflicting, or failed with error.
        """
        # 1. Check positive indicators for protection
        if is_prot_avail == AVAIL_AVAILABLE and is_prot_val is True:
            return PROTECTION_PROTECTED

        if states_avail == AVAIL_AVAILABLE and states_val is not None:
            try:
                prot_state = getattr(controlTypes.State, "PROTECTED", None)
                if prot_state is not None and (
                    prot_state in states_val or getattr(prot_state, "name", None) in states_val
                ):
                    return PROTECTION_PROTECTED
            except Exception:
                pass

        pwd_role = getattr(controlTypes.Role, "PASSWORDEDIT", None)
        if pwd_role is not None and role_val == pwd_role:
            return PROTECTION_PROTECTED

        if isinstance(raw_attrs, dict) and raw_attrs.get("type", "").lower() == "password":
            return PROTECTION_PROTECTED

        # 2. If checking isProtected resulted in an error, it is indeterminate
        if is_prot_avail == AVAIL_ERROR:
            return PROTECTION_INDETERMINATE

        # 3. Check positive indicators for non-protection
        if is_prot_avail == AVAIL_AVAILABLE and is_prot_val is False:
            return PROTECTION_UNPROTECTED

        if (
            is_prot_avail == AVAIL_UNAVAILABLE
            and states_avail == AVAIL_AVAILABLE
            and states_val is not None
            and role_val is not None
        ):
            return PROTECTION_UNPROTECTED

        # 4. Otherwise, evidence is missing/unavailable -> indeterminate
        return PROTECTION_INDETERMINATE

    def _check_is_protected(self, obj):
        """
        Verify whether the object is protected/password or indeterminate.
        Returns True if protected OR indeterminate (fails closed).
        Returns False only when non-protection is positively established.
        """
        is_prot_val, is_prot_avail = self._safe_read(obj, "isProtected")
        states_val = None
        states_avail = AVAIL_UNAVAILABLE
        try:
            states_val = getattr(obj, "states", None)
            if states_val is not None:
                states_avail = AVAIL_AVAILABLE
        except NotImplementedError:
            states_avail = AVAIL_UNSUPPORTED
        except Exception:
            states_avail = AVAIL_ERROR

        role_val, _ = self._safe_read(obj, "role")

        raw_attrs = {}
        try:
            ia2_val = getattr(obj, "IA2Attributes", None)
            if ia2_val is not None:
                raw_attrs = dict(ia2_val)
        except Exception:
            pass

        protection = self._evaluate_protection(
            is_prot_val, is_prot_avail, states_val, states_avail, role_val, raw_attrs
        )
        return protection != PROTECTION_UNPROTECTED

    def _computeNvdaRoleString(self, role):
        if role is None:
            return None
        try:
            enumName = controlTypes.Role(role).name
        except Exception:
            return str(role)

        ariaLike = NVDA_ROLE_TO_ARIA.get(enumName)
        if ariaLike:
            return "{} ({})".format(enumName, ariaLike)

        return enumName

    def _retrieve_relation(self, obj, rel_type_str, budget=None):
        """Bound Python target consumption; the NVDA provider may prefetch internally."""
        if budget is None:
            budget = {"targets_remaining": 8, "characters_remaining": 4000, "truncated": False}
        limit = budget["targets_remaining"]
        if limit <= 0 or budget["characters_remaining"] <= 0:
            budget["truncated"] = True
            return None, AVAIL_UNAVAILABLE, True
        query, availability = self._safe_read(obj, "_getIA2RelationTargetsOfType")
        if not callable(query):
            return None, availability if availability == AVAIL_ERROR else AVAIL_UNSUPPORTED, False
        try:
            targets = query(rel_type_str)
            iterator = iter(targets)
        except ValueError:
            return None, AVAIL_UNSUPPORTED, False
        except Exception:
            return None, AVAIL_ERROR, False
        summaries = []
        truncated = False
        saw_error = False
        try:
            for item in itertools.islice(iterator, limit + 1):
                if budget["targets_remaining"] <= 0 or budget["characters_remaining"] <= 0:
                    truncated = True
                    break
                budget["targets_remaining"] -= 1
                name, name_availability = self._safe_read(item, "name")
                role, role_availability = self._safe_read(item, "role")
                if name_availability == AVAIL_ERROR or role_availability == AVAIL_ERROR:
                    saw_error = True
                if isinstance(name, str):
                    cap = min(500, budget["characters_remaining"])
                    excerpt = name[:cap]
                    budget["characters_remaining"] -= len(excerpt)
                    truncated = truncated or len(name) > cap
                else:
                    excerpt = None
                summaries.append({"name": excerpt, "role": str(role) if role is not None else None})
        except ValueError:
            if not summaries:
                return None, AVAIL_UNSUPPORTED, False
            saw_error = True
        except Exception:
            saw_error = True
        budget["truncated"] = budget["truncated"] or truncated
        if summaries:
            return summaries, AVAIL_ERROR if saw_error else AVAIL_AVAILABLE, truncated
        return None if saw_error else [], AVAIL_ERROR if saw_error else AVAIL_UNAVAILABLE, truncated

    def _native_header_text(self, obj, attribute, budget):
        if budget["targets_remaining"] <= 0 or budget["characters_remaining"] <= 0:
            budget["truncated"] = True
            return create_observation(None, SOURCE_NVDA, AVAIL_UNAVAILABLE, truncated=True)
        budget["targets_remaining"] -= 1
        text, availability = self._safe_read(obj, attribute)
        if not isinstance(text, str):
            budget["targets_remaining"] += 1
            return create_observation(None, SOURCE_NVDA, availability)
        cap = min(500, budget["characters_remaining"])
        excerpt = text[:cap]
        budget["characters_remaining"] -= len(excerpt)
        truncated = len(text) > cap
        budget["truncated"] = budget["truncated"] or truncated
        return create_observation(excerpt, SOURCE_NVDA, availability, truncated=truncated)

    def _get_ia2_relations(self, obj, budget):
        relations = {}
        mapping = [
            ("labelledby", "labelledBy"),
            ("describedby", "describedBy"),
            ("controls", "controllerFor"),
            ("details", "details"),
            ("errormessage", "error"),
        ]
        for rel_key, rel_type_str in mapping:
            val, avail, truncated = self._retrieve_relation(obj, rel_type_str, budget)
            extra = {}
            if truncated:
                extra["truncated"] = True
            if avail == AVAIL_ERROR and val:
                extra["partial"] = True
            relations[rel_key] = create_observation(val, SOURCE_IA2_REL, avail, **extra)
        return relations

    def _parse_ia2_bool_attr(self, raw_attrs, *keys):
        for k in keys:
            if k in raw_attrs:
                val_str = str(raw_attrs[k]).strip().lower()
                if val_str in ("true", "1"):
                    return True, AVAIL_AVAILABLE
                elif val_str in ("false", "0"):
                    return False, AVAIL_AVAILABLE
                else:
                    return val_str, AVAIL_AVAILABLE
        return None, AVAIL_UNAVAILABLE

    def _build_aria_section(
        self,
        obj,
        rawAttrs,
        derivedAttrs,
        tag,
        explicitRole,
        nativeRole,
        nvdaRole,
        finalRole,
        reference_budget,
    ):
        aria = {
            "explicit_role": create_observation(
                explicitRole,
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if explicitRole else AVAIL_UNAVAILABLE,
            ),
            "native_role": create_observation(
                nativeRole,
                SOURCE_DERIVED,
                AVAIL_AVAILABLE if nativeRole else AVAIL_UNAVAILABLE,
            ),
            "nvda_role": create_observation(
                nvdaRole,
                SOURCE_NVDA,
                AVAIL_AVAILABLE if nvdaRole else AVAIL_UNAVAILABLE,
            ),
            "final_role": create_observation(
                finalRole,
                SOURCE_DERIVED,
                AVAIL_AVAILABLE,
            ),
            "tag": create_observation(
                tag,
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if tag else AVAIL_UNAVAILABLE,
            ),
            "id": create_observation(
                rawAttrs.get("id"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "id" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            "class_name": create_observation(
                rawAttrs.get("class"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "class" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            "raw_attributes": rawAttrs,
            "derived_attributes": derivedAttrs,
            # Explicit mapped IA2 attributes
            "live": create_observation(
                rawAttrs.get("live"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "live" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            "container_live": create_observation(
                rawAttrs.get("container-live"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "container-live" in rawAttrs else AVAIL_UNAVAILABLE,
                inherited=True,
            ),
            "atomic": create_observation(
                rawAttrs.get("atomic"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "atomic" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            "container_atomic": create_observation(
                rawAttrs.get("container-atomic"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "container-atomic" in rawAttrs else AVAIL_UNAVAILABLE,
                inherited=True,
            ),
            "relevant": create_observation(
                rawAttrs.get("relevant"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "relevant" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            "container_relevant": create_observation(
                rawAttrs.get("container-relevant"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "container-relevant" in rawAttrs else AVAIL_UNAVAILABLE,
                inherited=True,
            ),
            "current": create_observation(
                rawAttrs.get("current"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "current" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            "roledescription": create_observation(
                rawAttrs.get("roledescription"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "roledescription" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            "haspopup": create_observation(
                rawAttrs.get("haspopup"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "haspopup" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            "sort": create_observation(
                rawAttrs.get("sort"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "sort" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            "level": create_observation(
                rawAttrs.get("level") or rawAttrs.get("aria-level"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if ("level" in rawAttrs or "aria-level" in rawAttrs) else AVAIL_UNAVAILABLE,
            ),
            # Range values
            "range_now": create_observation(
                rawAttrs.get("valuenow"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "valuenow" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            "range_min": create_observation(
                rawAttrs.get("valuemin"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "valuemin" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            "range_max": create_observation(
                rawAttrs.get("valuemax"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "valuemax" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            "range_text": create_observation(
                rawAttrs.get("valuetext"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "valuetext" in rawAttrs else AVAIL_UNAVAILABLE,
            ),
            # Relations
            "relations": self._get_ia2_relations(obj, reference_budget),
        }
        return aria

    def _build_context_section(
        self, obj, raw_attrs, states_val, states_avail, pos_val, pos_avail, reference_budget
    ):
        visible_label = create_observation(
            None,
            SOURCE_DOM,
            AVAIL_UNAVAILABLE,
            declaring_element=None,
        )

        # Language: preserve empty string "", distinguish DOM declaration
        if "language" in raw_attrs:
            lang_val = raw_attrs["language"]
            lang_source = SOURCE_IA2_ATTR
            lang_avail = AVAIL_AVAILABLE
        elif "lang" in raw_attrs:
            lang_val = raw_attrs["lang"]
            lang_source = SOURCE_IA2_ATTR
            lang_avail = AVAIL_AVAILABLE
        else:
            lang_val, lang_avail = self._safe_read(obj, "language")
            lang_source = SOURCE_NVDA

        language_ctx = {
            "effective_language": create_observation(lang_val, lang_source, lang_avail),
            "declared_lang": create_observation(None, SOURCE_DOM, AVAIL_UNAVAILABLE),
            "direction": create_observation(
                raw_attrs.get("dir"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "dir" in raw_attrs else AVAIL_UNAVAILABLE,
            ),
        }

        # Form: native states vs IA2 attributes
        if states_avail == AVAIL_AVAILABLE and states_val is not None:
            req_val = False
            ro_val = False
            inv_val = False
            try:
                st_req = getattr(controlTypes.State, "REQUIRED", None)
                if st_req is not None and st_req in states_val:
                    req_val = True
            except Exception:
                pass
            try:
                st_ro = getattr(controlTypes.State, "READONLY", None)
                if st_ro is not None and st_ro in states_val:
                    ro_val = True
            except Exception:
                pass
            try:
                st_inv = getattr(controlTypes.State, "INVALID_ENTRY", None)
                if st_inv is not None and st_inv in states_val:
                    inv_val = True
            except Exception:
                pass
            req_obs = create_observation(req_val, SOURCE_NVDA, AVAIL_AVAILABLE)
            ro_obs = create_observation(ro_val, SOURCE_NVDA, AVAIL_AVAILABLE)
            inv_obs = create_observation(inv_val, SOURCE_NVDA, AVAIL_AVAILABLE)
        elif states_avail == AVAIL_ERROR:
            req_obs = create_observation(None, SOURCE_NVDA, AVAIL_ERROR)
            ro_obs = create_observation(None, SOURCE_NVDA, AVAIL_ERROR)
            inv_obs = create_observation(None, SOURCE_NVDA, AVAIL_ERROR)
        elif states_avail == AVAIL_UNSUPPORTED:
            req_obs = create_observation(None, SOURCE_NVDA, AVAIL_UNSUPPORTED)
            ro_obs = create_observation(None, SOURCE_NVDA, AVAIL_UNSUPPORTED)
            inv_obs = create_observation(None, SOURCE_NVDA, AVAIL_UNSUPPORTED)
        else:
            req_obs = create_observation(None, SOURCE_NVDA, AVAIL_UNAVAILABLE)
            ro_obs = create_observation(None, SOURCE_NVDA, AVAIL_UNAVAILABLE)
            inv_obs = create_observation(None, SOURCE_NVDA, AVAIL_UNAVAILABLE)

        aria_req_val, aria_req_avail = self._parse_ia2_bool_attr(raw_attrs, "aria-required", "required")
        aria_ro_val, aria_ro_avail = self._parse_ia2_bool_attr(raw_attrs, "aria-readonly", "readonly")
        aria_inv_val, aria_inv_avail = self._parse_ia2_bool_attr(raw_attrs, "aria-invalid", "invalid")

        form_ctx = {
            "input_type": create_observation(
                raw_attrs.get("type"),
                SOURCE_IA2_ATTR,
                AVAIL_AVAILABLE if "type" in raw_attrs else AVAIL_UNAVAILABLE,
            ),
            "required": req_obs,
            "readonly": ro_obs,
            "invalid": inv_obs,
            "aria_required": create_observation(aria_req_val, SOURCE_IA2_ATTR, aria_req_avail),
            "aria_readonly": create_observation(aria_ro_val, SOURCE_IA2_ATTR, aria_ro_avail),
            "aria_invalid": create_observation(aria_inv_val, SOURCE_IA2_ATTR, aria_inv_avail),
            "group_position": create_observation(pos_val, SOURCE_NVDA, pos_avail),
            "group_name": create_observation(None, SOURCE_NVDA, AVAIL_UNAVAILABLE),
            "pattern": create_observation(None, SOURCE_DOM, AVAIL_UNAVAILABLE),
            "minlength": create_observation(None, SOURCE_DOM, AVAIL_UNAVAILABLE),
            "maxlength": create_observation(None, SOURCE_DOM, AVAIL_UNAVAILABLE),
            "validation_message": create_observation(None, SOURCE_DOM, AVAIL_UNAVAILABLE),
        }

        # Table: guarded reads for native table APIs
        row_num, row_avail = self._safe_read(obj, "rowNumber")
        col_num, col_avail = self._safe_read(obj, "columnNumber")
        row_span, row_span_avail = self._safe_read(obj, "rowSpan")
        col_span, col_span_avail = self._safe_read(obj, "columnSpan")
        row_cnt, row_cnt_avail = self._safe_read(obj, "rowCount")
        col_cnt, col_cnt_avail = self._safe_read(obj, "columnCount")

        table_ctx = {
            "row_index": create_observation(row_num, SOURCE_NVDA, row_avail),
            "column_index": create_observation(col_num, SOURCE_NVDA, col_avail),
            "row_span": create_observation(row_span, SOURCE_NVDA, row_span_avail),
            "column_span": create_observation(col_span, SOURCE_NVDA, col_span_avail),
            "row_count": create_observation(row_cnt, SOURCE_NVDA, row_cnt_avail),
            "column_count": create_observation(col_cnt, SOURCE_NVDA, col_cnt_avail),
            "row_header_text": self._native_header_text(obj, "rowHeaderText", reference_budget),
            "column_header_text": self._native_header_text(obj, "columnHeaderText", reference_budget),
            "row_headers": create_observation(None, SOURCE_NVDA, AVAIL_UNAVAILABLE),
            "column_headers": create_observation(None, SOURCE_NVDA, AVAIL_UNAVAILABLE),
        }

        # Composite: guarded states check
        if states_avail == AVAIL_AVAILABLE and states_val is not None:
            sel_val = False
            foc_val = False
            try:
                st_sel = getattr(controlTypes.State, "SELECTED", None)
                if st_sel is not None and st_sel in states_val:
                    sel_val = True
            except Exception:
                pass
            try:
                st_foc = getattr(controlTypes.State, "FOCUSED", None)
                if st_foc is not None and st_foc in states_val:
                    foc_val = True
            except Exception:
                pass
            sel_obs = create_observation(sel_val, SOURCE_NVDA, AVAIL_AVAILABLE)
            foc_obs = create_observation(foc_val, SOURCE_NVDA, AVAIL_AVAILABLE)
        elif states_avail == AVAIL_ERROR:
            sel_obs = create_observation(None, SOURCE_NVDA, AVAIL_ERROR)
            foc_obs = create_observation(None, SOURCE_NVDA, AVAIL_ERROR)
        elif states_avail == AVAIL_UNSUPPORTED:
            sel_obs = create_observation(None, SOURCE_NVDA, AVAIL_UNSUPPORTED)
            foc_obs = create_observation(None, SOURCE_NVDA, AVAIL_UNSUPPORTED)
        else:
            sel_obs = create_observation(None, SOURCE_NVDA, AVAIL_UNAVAILABLE)
            foc_obs = create_observation(None, SOURCE_NVDA, AVAIL_UNAVAILABLE)

        composite_ctx = {
            "owning_composite_role": create_observation(None, SOURCE_NVDA, AVAIL_UNAVAILABLE),
            "is_selected": sel_obs,
            "is_focused": foc_obs,
            "active_descendant": create_observation(None, SOURCE_DOM, AVAIL_UNAVAILABLE),
        }

        return {
            "visible_label": visible_label,
            "language": language_ctx,
            "form": form_ctx,
            "table": table_ctx,
            "composite": composite_ctx,
        }

    def getRawAttrs(self, obj):
        """
        Return IA2 attributes only.

        Important: this does not include attributes derived from NVDA states.
        """
        attrs = {}

        try:
            ia2 = getattr(obj, "IA2Attributes", None)

            if ia2 is not None:
                attrs = dict(ia2)
        except Exception:
            self._logDebug("Could not read IA2Attributes")

        is_prot = self._check_is_protected(obj)
        if is_prot:
            attrs.pop("value", None)

        try:
            tag = attrs.get("tag", "")

            if not is_prot:
                if tag == "a" and getattr(obj, "value", None) and "href" not in attrs:
                    attrs["href"] = obj.value

                elif tag == "#document" and getattr(obj, "value", None) and "document-url" not in attrs:
                    attrs["document-url"] = obj.value
        except Exception:
            self._logDebug("Could not derive href or document-url from object value")

        return attrs

    def getStateBasedAttrs(self, obj):
        """
        Return ARIA-like attributes derived from NVDA states.

        These are not raw DOM attributes.
        """
        result = {}

        try:
            states = obj.states
        except Exception:
            return result

        for stateName, ariaAttr, ariaValue in STATE_TO_ARIA:
            try:
                state = getattr(controlTypes.State, stateName, None)

                if state is not None and state in states:
                    if ariaAttr not in result:
                        result[ariaAttr] = ariaValue
            except Exception:
                self._logDebug("Could not process state: {}".format(stateName))

        return result

    def getAccessibleName(self, obj):
        try:
            name = obj.name

            if name:
                return name

            return ""
        except Exception:
            self._logDebug("Could not read accessible name")
            return None

    def getNameSource(self, obj, attrs, name=None):
        if "aria-labelledby" in attrs:
            return "aria-labelledby", "certain"

        if "aria-label" in attrs:
            return "aria-label", "certain"

        nameFrom = attrs.get("name-from", "")

        if nameFrom == "value":
            return "value", "certain"

        if nameFrom == "contents":
            return "contents", "certain"

        if nameFrom == "related element":
            return "related element", "inferred"

        if nameFrom == "attribute":
            tag = attrs.get("tag", "").strip().lower()

            if "alt" in attrs:
                return "alt", "certain"

            if "title" in attrs:
                return "title", "inferred"

            if "placeholder" in attrs:
                return "placeholder", "inferred"

            if "value" in attrs:
                if tag in ("input", "button"):
                    return "value", "certain"

                return "value", "inferred"

            return "attribute", "inferred"

        if name is not None:
            if name:
                return "unknown computed source", "unknown"
        else:
            try:
                if obj is not None and getattr(obj, "name", None):
                    return "unknown computed source", "unknown"
            except Exception:
                pass

        return "none detected", "unknown"

    def getExplicitRole(self, attrs):
        role = attrs.get("xml-roles", "").strip()

        if not role:
            return None

        return role

    def getNvdaRole(self, obj):
        try:
            role = obj.role
        except Exception:
            self._logDebug("Could not read NVDA role")
            return None

        try:
            enumName = controlTypes.Role(role).name
        except Exception:
            return str(role)

        ariaLike = NVDA_ROLE_TO_ARIA.get(enumName)

        if ariaLike:
            return "{} ({})".format(enumName, ariaLike)

        return enumName

    def getFinalRole(self, explicitRole, nativeRole, nvdaRole):
        if explicitRole:
            return explicitRole

        if nativeRole:
            return nativeRole

        if nvdaRole:
            return nvdaRole

        return "unknown"

    def getSemanticSource(self, explicitRole, nativeRole, tag):
        if not tag:
            return "unknown"

        if explicitRole and nativeRole:
            if explicitRole.lower() == str(nativeRole).lower():
                return "redundant explicit role"

            if nativeRole in ("none", "presentation"):
                return "explicit role removes native semantics"

            return "explicit role overrides native HTML"

        if explicitRole and not nativeRole:
            return "explicit role on non-semantic element"

        if nativeRole:
            if str(nativeRole).endswith("?"):
                return "native HTML, context-dependent"

            return "native HTML"

        return "no native semantics detected"

    def getNativeSemanticMismatch(self, explicitRole, nativeRole, tag):
        if not tag:
            return "unknown"

        if not explicitRole and not nativeRole:
            return "not applicable"

        if explicitRole and not nativeRole:
            return "no native role to mismatch; explicit role used"

        if nativeRole and not explicitRole:
            return "no"

        if nativeRole and explicitRole:
            if explicitRole.lower() == str(nativeRole).lower():
                return "no; explicit role is redundant"

            return "yes; explicit role differs from native role"

        return "unknown"

    def buildDomPath(self, obj, maxDepth=25, initialAttrs=None):
        parts = []
        current = obj
        depth = 0

        while current is not None and depth < maxDepth:
            depth += 1

            if depth == 1 and initialAttrs is not None:
                attrs = initialAttrs
            else:
                attrs = self.getRawAttrs(current)
            tag = attrs.get("tag", "").strip().lower()

            if not tag:
                break

            if tag == "#document":
                break

            parts.append(self.domPathSegment(attrs))

            try:
                current = current.parent
            except Exception:
                break

        parts.reverse()
        return " > ".join(parts)

    def domPathSegment(self, attrs):
        tag = attrs.get("tag", "").strip().lower()

        if not tag:
            return "unknown"

        segment = tag

        nodeId = attrs.get("id", "").strip()

        if nodeId:
            return '{}[id="{}"]'.format(segment, self._escapeSelectorPart(nodeId))

        classAttr = attrs.get("class", "").strip()

        if classAttr:
            classes = [c for c in classAttr.split() if c]

            if classes:
                classPart = "".join('[class~="{}"]'.format(self._escapeSelectorPart(c)) for c in classes[:2])
                return "{}{}".format(segment, classPart)

        nameAttr = attrs.get("name", "").strip()

        if nameAttr:
            return '{}[name="{}"]'.format(
                segment,
                self._escapeSelectorPart(nameAttr),
            )

        roleAttr = attrs.get("xml-roles", "").strip()

        if roleAttr:
            return '{}[role="{}"]'.format(
                segment,
                self._escapeSelectorPart(roleAttr),
            )

        return segment

    def ancestors(self, obj, maxDepth=20):
        result = []

        try:
            current = obj.parent
        except Exception:
            return result

        depth = 0

        while current is not None and depth < maxDepth:
            depth += 1

            try:
                attrs = self.getRawAttrs(current)
                tag = attrs.get("tag")
            except Exception:
                tag = None

            if tag:
                result.append(current)

                if tag == "#document":
                    break

            try:
                current = current.parent
            except Exception:
                break

        return result

    def getMsaaRole(self, obj):
        try:
            iaObj = getattr(obj, "IAccessibleObject", None)
            childId = getattr(obj, "IAccessibleChildID", 0)

            if iaObj:
                return iaObj.accRole(childId)
        except Exception:
            self._logDebug("Could not read MSAA role")

        return None

    def _escapeSelectorPart(self, value):
        return str(value).replace("\\", "\\\\").replace('"', '\\"')

    def _logDebug(self, message):
        if log is not None:
            try:
                log.debugWarning(message, exc_info=True)
            except Exception:
                pass
