# -*- coding: utf-8 -*-
"""
Serializable snapshot contract and observation utilities.

Defines the plain-dictionary snapshot contract with provenance
and explicit availability as specified in Phase 0 of plan.md.
Compatible with Python 3.7+ (NVDA 2023.1+ runtime floor).
"""

from typing import Any, Dict, Iterable, List, Mapping, Optional, Union, cast
import uuid

# Observation Sources
SOURCE_NVDA: str = "nvda"
SOURCE_IA2_ATTR: str = "ia2_attribute"
SOURCE_IA2_REL: str = "ia2_relation"
SOURCE_DOM: str = "dom"
SOURCE_DERIVED: str = "derived"

# Observation Availability States
AVAIL_AVAILABLE: str = "available"
AVAIL_UNAVAILABLE: str = "unavailable"
AVAIL_UNSUPPORTED: str = "unsupported"
AVAIL_ERROR: str = "error"

# Protection States
PROTECTION_PROTECTED: str = "protected"
PROTECTION_UNPROTECTED: str = "unprotected"
PROTECTION_INDETERMINATE: str = "indeterminate"

ObservationValue = Optional[
    Union[bool, int, float, str, List[Any], Dict[str, Any]]
]


def create_observation(
    value: Any,
    source: str,
    availability: str,
    **extra: Any,
) -> Dict[str, Any]:
    """
    Create a property observation dictionary.

    Preserves false, zero, and known empty string as distinct values.
    Ensures JSON serializability.
    """
    obs: Dict[str, Any] = {
        "value": sanitize_value(value),
        "source": str(source),
        "availability": str(availability),
    }
    for k, v in extra.items():
        obs[str(k)] = sanitize_value(v)
    return obs


def create_empty_snapshot(
    request_id: Optional[Union[str, int]] = None,
) -> Dict[str, Any]:
    """
    Create a plain-dictionary snapshot structure with the 8 top-level sections.
    """
    req_id = str(request_id) if request_id is not None else str(uuid.uuid4())
    return {
        "target": {
            "request_id": req_id,
            "target_identity": {},
            "document_identity": None,
            "frame_identity": None,
            "element_identity": None,
        },
        "native": {},
        "aria": {},
        "dom": {
            "source": SOURCE_DOM,
            "availability": AVAIL_UNAVAILABLE,
            "attributes": {},
            "properties": {},
        },
        "layout": {
            "source": SOURCE_DOM,
            "availability": AVAIL_UNAVAILABLE,
            "bounds": None,
            "styles": {},
        },
        "context": {},
        "audit": [],
        "availability": {
            "native": AVAIL_AVAILABLE,
            "ia2": AVAIL_UNAVAILABLE,
            "bridge": AVAIL_UNAVAILABLE,
        },
    }


def sanitize_value(val: Any) -> ObservationValue:
    """
    Sanitize values to ensure JSON-serializability without crashing.
    Converts collections, sets, tuples, and non-primitives to safe types.
    """
    if val is None or isinstance(val, (bool, int, float, str)):
        return val
    if isinstance(val, (list, tuple, set)):
        seq = cast(Iterable[Any], val)
        return [sanitize_value(item) for item in seq]
    if isinstance(val, dict):
        mapping = cast(Mapping[Any, Any], val)
        return {str(k): sanitize_value(v) for k, v in mapping.items()}
    # Fallback to string representation for non-serializable objects
    try:
        return str(val)
    except Exception:
        return None
