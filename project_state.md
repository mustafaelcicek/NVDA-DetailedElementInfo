# Project State

Updated: 2026-10-19

## Current Work

- 2026-10-19: Resolved Python 3.7 runtime typing blocker on `snapshot.py`. Replaced PEP 604 union (`|`) and PEP 585 builtin collection generics (`list[Any]`, `dict[str, Any]`) with standard `typing.Union`, `typing.Optional`, `typing.Dict`, `typing.List`, `typing.Mapping`, and `typing.Iterable` constructs to support the NVDA 2023.1 runtime floor (Python 3.7). Resolved dynamic collection typing diagnostics with boundary casts. Added scenario 21 (Regression 10) checking AST and runtime typing compatibility.
- 2026-10-18: Phases 0 and 1 (serializable snapshot contract and native NVDA/IA2 property expansion) repaired following Codex review findings 1-10. Standalone runner (`scripts/run_tests.py`) verified 20 targeted scenarios across snapshot structure, empty/zero/false preservation, tri-state protection, raw attribute sanitization, guarded independent reads, single-capture root property reuse, relation generator bounded consumption, official relation names, form context boolean fidelity, language empty string preservation, and unique UUID capture IDs.

## Decisions

- Support NVDA 2023.1 runtime floor (Python 3.7) in all production add-on code under `addon/`. Build-tooling requirements in `pyproject.toml` (>=3.13) govern developer linting/packaging tools only, not add-on runtime execution.
- In `snapshot.py`, use Python 3.7-compatible `typing` constructs: `ObservationValue = Optional[Union[bool, int, float, str, List[Any], Dict[str, Any]]]`, `Dict[str, Any]`, and boundary `cast` for dynamic iterables/mappings in `sanitize_value`.
- Preserve the full feature scope while ordering work as contract, native properties, verified Bridge enrichment, bounded audit/contrast, shared reports, explicit Gemini analysis, documentation reconciliation, and acceptance.
- Use a single sanitized snapshot for one captured inspection target; capture root provider properties ONCE during snapshot construction and derive target identity, native section, aria section, context, and legacy compatibility fields from the captured snapshot without redundant live re-reads.
- Implement explicit tri-state protection logic (`PROTECTION_PROTECTED`, `PROTECTION_UNPROTECTED`, `PROTECTION_INDETERMINATE`). Positive non-protection must be established before reading `obj.value`; bare/indeterminate objects never read `obj.value`.
- Redact/strip private `"value"` from IA2 attributes (`rawAttrs` and `aria.raw_attributes`) whenever protection is protected or indeterminate, preventing password leakage into serialized snapshots and HTML reports while preserving unrelated attributes.
- Use guarded reads (`_safe_read`) catching `NotImplementedError` as `unsupported` and other exceptions as `error` across all provider boundaries (`name`, `role`, `positionInfo`, table coordinates, `IA2Attributes`).
- Consume IA2 relation generators boundedly using `itertools.islice`, capping at 8 items and recording `truncated=True` if a 9th item exists; wrap streaming iteration to preserve partial results upon deferred stream errors.
- Query official NVDA 2026.1 `RelationType` names: `controls` queries `controllerFor` (`RelationType.CONTROLLER_FOR`), `errormessage` queries `error` (`RelationType.ERROR`), `labelledby` queries `labelledBy`, and `details` queries `details`. Treat unsupported types (such as `describedBy`) as `unsupported`.
- Preserve separately sourced native states and IA2 attributes in form context; parse explicit string `"false"` to `False` rather than `True`, and mark unreadable native states as `unavailable`/`error` rather than inventing `False`.
- In language context, preserve explicit empty string `""` as available, and keep `declared_lang` marked as `source="dom", availability="unavailable"` in native milestone until DOM inspection is active.
- Generate unique UUID4 capture IDs (`str(uuid.uuid4())`) to avoid timestamp collisions.
- Keep `analyzer.analyze(obj)` backwards compatible: returns legacy flat keys derived from the snapshot while attaching `"snapshot": snapshot`.
- Add minimal compatibility seam to `ReportBuilder.buildReport` and `_formatElement` to accept legacy analyzed dictionaries carrying a snapshot and live NVDAObjects. Direct snapshot rendering is reserved for Phase 4.

## Evidence and Limits

- Local verification completed:
  - `scripts/run_tests.py`: 24 passed, 0 failed, exit code 0.
  - `uv run --no-sync pyright --pythonversion 3.7 addon/globalPlugins/detailedElementInfo/snapshot.py`: 0 errors, 0 warnings, exit code 0.
  - `uv run --no-sync ruff check addon/ scripts/`: 0 errors on changed files; 11 pre-existing E402 reports on `addon/__init__.py`.
  - `uv run --no-sync pyright --outputjson`: 12 files analyzed, total 1285 errors across 11 files (exit code 1; baseline 726 over 10 files):
    - `__init__.py`: 114 (baseline)
    - `ai_handler.py`: 17 (baseline)
    - `config.py`: 22 (baseline)
    - `debug.py`: 6 (baseline)
    - `elementAnalyzer.py`: 422 (new helper diagnostics remain; not solely missing NVDA stubs)
    - `reportBuilder.py`: 177 (baseline)
    - `roleMaps.py`: 53 (baseline)
    - `server.py`: 14 (baseline)
    - `settingsPanel.py`: 139 (baseline)
    - `snapshot.py`: 15 (all 15 are `reportDeprecated` under Python 3.13 tooling config; 0 errors under Python 3.7 runtime check)
    - `scripts/run_tests.py`: 306 (new test runner with dynamic mocks)
  - `git diff --check`: exit code 0 (clean).
  - `uv run --no-sync scons`: exit code 0 (`detailedElementInfo-1.1.0.nvda-addon` generated).
- Code written and local verification passed does not equal human NVDA acceptance; testing in real NVDA on Windows remains mandatory.

## Next Step

Native local review is complete after four reviewer repairs: captured safe URL derivation retained for legacy reports; language read guarded once; incomplete relation summaries carry error/partial evidence; missing captured names are not re-read. Regression runner reproduced four failures before repairs and passes 24/24 afterward. Phase 2 may proceed under existing authorization; human NVDA acceptance remains pending, as do Phases 2-7.
