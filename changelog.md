# Changelog

- 2026-10-19: Restrict DOM enrichment to positively identified Chrome targets in a focused window; invalidate all document witnesses and pending delivery on window-focus changes.

- 2026-10-19: Analyze only the explicitly selected report snapshot through a bounded Gemini allowlist, redact duplicated sensitive text, omit editable text without value evidence, and keep errors free of credentials/response bodies; preserve locale and local offline features.

- 2026-10-19: Render frozen evidence in matching HTML/Markdown sections, preserve four section settings and old choices, and bind unassigned Markdown copying to each report snapshot with verified clipboard success. Human NVDA acceptance remains pending.

- 2026-10-19: Add deterministic, sourced per-element name/image/label/click checks and conservative production-JavaScript text contrast; preserve unknown applicability and meaningful mathematical symbols. Human NVDA acceptance remains pending.

- 2026-10-19: Repair Bridge document binding, protected-data omission, shared reference budgets and contextual evidence directly after independent review; retain 49 local scenarios and 18 optional production-JavaScript Chrome checks. Human NVDA acceptance remains pending.

- 2026-10-19: Reject the Phase 2A repair after independent review confirmed remaining document-binding, schema, protected-markup and advisory-message defects; retain the draft uncommitted and await the user's choice before a third attempt.
- 2026-10-19: Repair native snapshot review regressions in safe link URL reuse, guarded language reads, partial relation evidence, and single-capture missing names; add focused regression cases.

All notable changes to this project will be documented in this file.

## Implementation - 2026-10-19

- Draft Phase 2 Bridge collection and lifecycle changes; neither the initial delivery nor its Phase 2A repair passed independent review.
- Preserve the verified URL query/path, duplicate-ID, generation-invalidation and deepcopy improvements; document the remaining binding, privacy, context and shared-budget defects in project_state.md.
- Expand the standalone runner to 42 passing scenarios and add real-source JavaScript helper tests; independent probes still expose failures outside their coverage.
- Resolve Python 3.7 runtime typing compatibility blocker in `snapshot.py` to support NVDA 2023.1 runtime floor: replace PEP 604 unions (`|`) and PEP 585 builtin collection generics with standard `typing.Union`, `Optional`, `Dict`, `List`, `Mapping`, and `Iterable` constructs.
- Add boundary casts in `sanitize_value` to resolve dynamic collection typing diagnostics under strict Pyright checks without blanket ignores.
- Add Regression 10 to `scripts/run_tests.py` verifying AST-level and runtime compatibility for Python 3.7 (21/21 passing scenarios).

## Implementation - 2026-10-18

- Implement Phase 0 snapshot contract with explicit provenance and availability states (`available`, `unavailable`, `unsupported`, `error`) and UUID capture IDs in `snapshot.py`.
- Implement Phase 1 native NVDA and IA2 property expansion in `elementAnalyzer.py`: single-capture root property architecture, tri-state protection with fail-closed value omission, password value redaction from `rawAttrs`, guarded independent property reads, explicit mapped IA2 attributes with container separation, generator-tolerant IA2 relations bounded to 8 items with official RelationType names, and five verified native context groups (`visible_label`, `language`, `form`, `table`, `composite`).
- Introduce minimal backward-compatibility seam in `reportBuilder.py` accepting both pre-analyzed snapshot dicts and live NVDAObjects.
- Expand standalone scenario runner `scripts/run_tests.py` to 20 targeted scenarios covering all initial specifications and Codex review regression checks.

## Delegation - 2026-10-18

- Prepare Antigravity implementation and record baseline gates; headless command approval blocked the first dispatch before source edits.

## Planning - 2026-10-18

- Correct the expansion plan's data contract, diagnostic rules, contrast limits, privacy boundaries, and acceptance gates; no implementation changes.
- 2026-10-18: Add tester context requirements and a separately deferred focus/live-announcement observation extension to the plan; no implementation changes.

## [1.1.0] - 2026-07-29

### Added

- **Chrome Bridge:** Added a Manifest V3 companion extension that retrieves the active page's live DOM attributes and properties instead of relying only on NVDA's virtual buffer.
- **On-demand AI analysis:** Added Google Gemini analysis with Alt+F1, using the user's own API key and responding in the active NVDA language.
- **Ukrainian localization:** Added complete Ukrainian interface and documentation translations.
- **Release package:** Tagged releases now include `detailedElementInfo-chrome-bridge.zip` alongside the NVDA add-on package.

### Changed

- Improved matching between the focused NVDA object and its corresponding DOM element using accessible names, IA2 identifiers, roles, dimensions, and DOM paths.
- Expanded gettext coverage for settings labels, analyzer statuses, report values, and AI messages.
- Completed and corrected the Turkish and Ukrainian translations, removing mixed-language report output.
- Updated Gemini integration to use `gemini-2.5-flash` and request responses in the current NVDA language.
- Displayed AI results in an escaped, structured HTML report.

### Security

- Redacted password-field values before DOM data leaves the Chrome Bridge.
- Restricted the local Bridge server to Chrome-extension origins instead of allowing arbitrary browser origins.
- Escaped AI-generated content before displaying it as HTML.

### Fixed

- Fixed incomplete translation initialization and mixed-language output reported in issue #3.
- Improved Chrome service-worker reconnection and error handling when the Bridge or active page is unavailable.
- Prevented generated Python cache files from being included in local add-on packages.

## [1.0.2] - 2026-07-15

### Changed

- Migrated the project to the NV Access add-on template and SCons build system.
- Moved generated manifests, compiled translations, and HTML documentation into the automated build process.
