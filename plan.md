# Comprehensive Element Information Expansion Implementation Plan

> For agentic workers: implement one milestone at a time using the repository's approved workflow. Review each milestone before advancing; subagent-driven development may divide planning, implementation, and verification according to model capacity. The human subsequently authorized implementation through Antigravity and independent review. Prepare Phases 0-7 sequentially; live NVDA acceptance remains a separate human gate.

**Goal:** Expand native accessibility information and optional Chrome DOM inspection, then present bounded diagnostic checks consistently in HTML, Markdown, and explicitly requested Gemini analysis.

**Architecture:** Capture the NVDA inspection target once, enrich it with a verified Bridge response when available, and freeze one sanitized snapshot. Audit and render that snapshot without fetching another element. Keep the existing add-on and Bridge architecture; add only the small audit module and lightweight verification fixtures needed by this plan.

**Tech stack:** Python standard library, NVDA APIs, existing Chrome Manifest V3 Bridge, and existing SCons tooling. No new runtime packages, services, or model SDKs.

**Spec:** This document incorporates the 2026-10-18 review; repository constraints are in [AGENTS.md](AGENTS.md), [CLAUDE.md](CLAUDE.md), and [CONTRIBUTING.md](CONTRIBUTING.md).

**Status:** Direct reviewer repair of Phases 1-2 is locally verified (49 scenarios, 18 actual Chrome cases and independent review); human NVDA acceptance remains pending. Phase 3 is locally verified (54 scenarios and 37 actual Chrome cases) after independent review. Phase 4 is in progress; Phases 5-7 and human NVDA acceptance remain pending.

## Global Constraints

- Preserve the zero-third-party-runtime-dependency policy. Existing development/build tools are not add-on runtime dependencies.
- Target NVDA 2023.1 and newer, including the 2026.1 Python 3.13/64-bit transition. Treat compatibility as a requirement to verify, not an established result of this plan.
- Preserve existing user configuration, defaults for existing fields, version numbers, buildVars.py metadata, release metadata, and locale files. No unrelated refactoring.
- Translate new visible text through NVDA's translation system. Bridge returns stable keys and raw data; Python supplies translated labels. Separate display messages from machine-readable rule identifiers.
- Update English readme.md and addon/doc/tr/readme.md with each user-visible milestone; Phase 6 checks their final agreement. Never edit generated readme.html files.
- Use imperative English Conventional Commit titles, one logical change per commit, and no AI co-author trailers. Do not commit unless authorized.
- Human NVDA testing is mandatory before proposing the change. Agents must not open, submit, or merge PRs or push to main; provide a PR draft for the human.
- Preserve the existing explicit Alt+F1 boundary for Google requests. Report display and Markdown copying must work offline and must not invoke Gemini.
- Keep task.md, project_state.md, and changelog.md current during authorized implementation. No claim of live behavior without a recorded human result.

## Review Focus

- A late Bridge response belongs to a different element, document, frame, or request: reject it and retain native information.
- A property is missing, unsupported, stale, or inaccessible: represent its availability explicitly rather than substituting false, zero, or an empty value.
- A heuristic appears to identify a WCAG problem: distinguish a supported failure from a warning, an unknown result, and a rule that does not apply.
- A password value or editable user content enters a new output path: sanitize before HTML, Markdown, and AI export; never log payloads or API keys.
- Existing settings hide fields: preserve those choices across both report formats, Select all / Clear all, and upgrades.

## Phase 0: Define the Snapshot Contract and Baseline

**Suggested commit:** docs: define element inspection data and acceptance contracts

**Files:** plan.md; task.md; project_state.md. Later implementation inventory is limited to files named by the owning phases.

- [ ] Confirm documented entry points and existing Bridge transport responsibilities before implementation. Proposed interfaces below are design decisions, not claims that methods already exist. Verify actual signatures at the implementation boundary; obtain clarification if repository constraints prevent the inspection needed to change them safely.
- [ ] Record a baseline human scenario for the current report, settings, Bridge, and explicit Gemini request before changing behavior.
- [ ] Use a plain-dictionary snapshot with these top-level sections: target, native, aria, dom, layout, context, audit, availability. Do not introduce a new framework or persistence layer.
- [ ] target carries a request ID, the captured NVDA target identity, and verified document/frame/element identity when the Bridge supports it. Preserve browse-mode inspection of the review/caret target; do not substitute document.activeElement.
- [ ] Each newly collected property records value, source (nvda, ia2_attribute, ia2_relation, or dom), and availability (available, unavailable, unsupported, or error). A known empty string is available data; unavailable is not an empty string. Preserve conflicting raw and computed values under distinct keys.
- [ ] context has five bounded groups: visible_label, language, form, table, and composite. Each contextual observation retains the same value/source/availability contract, plus the declaring or related element identity where known. Preserve absence, empty declarations, unresolved inheritance, and unsupported tree scopes as different observations.
- [ ] Additional context does not expand the Phase 5 AI allowlist automatically. Relationship/header/group excerpts share Phase 2's existing excerpt and target budgets; truncation makes unexamined associations unknown, not absent.
- [ ] Audit findings use rule_id, status, message_key, evidence, source, and wcag_refs. Allowed status values are pass, warning, fail, unknown, and not_applicable. pass applies only to the stated check and never establishes overall WCAG conformance.
- [ ] Freeze the sanitized snapshot after enrichment. The audit evaluates it; HTML, Markdown, and the optional AI request consume the same result. Renderers must not read the live NVDA object or requery Chrome.

**Acceptance:** A documented sample snapshot distinguishes a known empty name, an unavailable DOM attribute, a conflicting computed value, and a stale response. All later phases use the same keys and status meanings.

## Phase 1: Expand Native ARIA and NVDA Properties

**Suggested commit:** feat: expand native element accessibility properties

**Files:** addon/globalPlugins/detailedElementInfo/elementAnalyzer.py; roleMaps.py only if an evidenced mapping change is needed; scripts/run_tests.py; both user readmes.

- [ ] Read obj.description, obj.keyboardShortcut, obj.positionInfo, and applicable obj.value independently, with per-property exception handling. Preserve zero and false values. Suppress protected/password values before they enter the snapshot.
- [ ] Map IA2 attribute names explicitly; do not assume literal aria-* keys. Examples include live/container-live, atomic, relevant, current, and roledescription. Label inherited container values separately from properties of the inspected element.
- [ ] Retrieve supported relations for labelledby, describedby, controls, details, and errormessage through verified NVDA/IA2 APIs. Preserve the distinction between exposed relations and original DOM IDREF text. aria-owns may change accessible-tree ownership rather than survive as a raw attribute.
- [ ] Keep range values, live-region properties, interactive states, and native group position distinct from source DOM attributes. Do not infer that a missing IA2 relation proves an absent or broken DOM reference.
- [ ] Where verified native APIs expose them, collect effective language, form/group context, cell coordinates/spans and associated row/column headers, and composite focus/selection relationships. Native group position is not a substitute for table coordinates. Preserve declared DOM values separately from accessibility-API values and mark unsupported native observations explicitly.
- [ ] Keep native-only inspection useful when the object lacks IA2 or a property raises an exception; mark individual fields unavailable or unsupported.
- [ ] Add focused checks to scripts/run_tests.py for empty/zero/false values, a failing property getter, missing IA2, and relation data without raw DOM IDs.

**Acceptance:** Native-only output retains all existing fields and preserves their meanings; new properties have explicit provenance. A human verifies representative controls in NVDA before the next milestone is accepted.

## Phase 2: Enrich the Captured Target through Chrome Bridge

**Suggested commit:** feat: enrich verified element snapshots through Chrome bridge

**Files:** Bridge/content.js; Bridge/background.js, Bridge/inject.js, addon/globalPlugins/detailedElementInfo/server.py, elementAnalyzer.py, and __init__.py only where required by the actual transport and command path; scripts/element_info_fixture.html; scripts/run_tests.py; both user readmes.

- [ ] Correlate each response with the captured request and verified document/frame/element. Reject ambiguous matches and responses for superseded requests, changed navigation, disconnected targets, or closed reports. Reuse reliable existing matching and timeout behavior; do not alter user-configured limits.
- [ ] Keep Bridge I/O off NVDA's UI thread and use NVDA-supported dispatch for NVDA object/UI work. Every request has a finite deadline; without an existing limit, use an initial two-second deadline and record this choice. Timeout or unsupported pages yield a native-only snapshot, never a blocking report or a claimed DOM result.
- [ ] Read raw ARIA attributes, including ordered IDREF tokens for labelledby, describedby, details, errormessage, controls, and owns. Record each target's resolution status and bounded text excerpt. Resolve in the correct document/tree scope; mark unsupported shadow-root and frame cases explicitly.
- [ ] Call excerpt text a referenced-target excerpt, not a computed accessible name or description. Use NVDA's accessible name/description separately; do not recreate AccName with textContent.trim(). Preserve missing-ID evidence without treating inaccessible tree scopes as broken references.
- [ ] Collect associated label information, including wrapping labels and multiple labels, along with relevant input types. Do not conflate visible labels with accessible-name computation.
- [ ] Populate context.visible_label with a bounded visible-label candidate, its source element, and evidence of applicability. Do not identify the label by blindly joining textContent or nearby text; image-only labels and ambiguous visual associations remain unknown. Keep the computed accessible name independent.
- [ ] Populate context.language with the element's raw lang declaration, the effective inherited language, and its declaring ancestor when resolvable. An explicit empty lang stops inheritance and denotes unknown language. Record declared dir, effective HTML directionality where determinable, and computed CSS direction separately; do not infer language from direction or claim correct language from a valid tag alone.
- [ ] Populate context.form with input type, required/aria-required, readonly/aria-readonly, aria-invalid, pattern, min/max/step, minlength/maxlength, and available browser validity flags, willValidate, and validationMessage. Distinguish absent constraints from browser defaults and current validity from the user's experience of validation. Read properties only: never call checkValidity(), reportValidity(), submit(), or mutate focus/input values.
- [ ] Include the nearest applicable form and fieldset/legend or ARIA group/radiogroup name, relevant group instructions, and their source identities. Resolve ancestor context within existing traversal bounds; if no bound exists, use an initial 32-ancestor limit and mark incomplete searches unknown. Apply existing excerpt caps and redaction to validation messages and group text, which may echo user input.
- [ ] Populate context.table for cells/headers with owning table/grid identity and name, row/column index and count, row/column spans, sort state, and actual exposed row/column header relationships when available. Preserve declared aria-rowindex/colindex/count/span, native/DOM observations, and inferred values separately; normalize displayed indices to one-based values with provenance. A count of -1 means unknown total, not a negative-size table.
- [ ] Resolve explicit headers IDREFs and supported header associations within the existing relationship budget. Do not equate scope or headers attributes alone with verified correct headers; complex implicit associations and virtualized/absent DOM cells remain unknown when evidence is incomplete. Do not reconstruct or scan the entire table merely to inspect one cell.
- [ ] Populate context.composite with the owning composite identity/role, captured DOM-focused element, aria-activedescendant tokens and resolved target, and applicable selected state on inspected/related elements. Preserve the distinction between DOM focus, active descendant, selection, and the NVDA review target; do not replace the inspection target or enumerate an entire widget to claim a complete selection list.
- [ ] Collect tabIndex, native semantics, isContentEditable, disabled, hidden/inert ancestry, and applicable computed visibility. Distinguish programmatic focusability from Tab-sequence membership; tabIndex alone proves neither full keyboard operation nor an accessibility failure.
- [ ] Record bounding rectangle coordinates in CSS pixels relative to that frame's viewport. Report viewport intersection separately from rendered visibility and occlusion; do not claim getBoundingClientRect proves visibility.
- [ ] Collect color, backgroundColor, backgroundImage, fontSize, fontWeight, and relevant opacity/compositing flags for Phase 3. Do not yet label an unresolved visual result a contrast failure.
- [ ] Cap each new relationship excerpt at 500 characters, inspect at most eight referenced targets per snapshot, and cap combined excerpt text at 4,000 characters. Mark truncation; unexamined targets remain unknown. Do not scan unrelated DOM subtrees.
- [ ] Sanitize newly collected raw attributes and values before serialization. Exclude password values and password markup through every representation, preserve existing origin restrictions, and do not broaden extension permissions without a reviewed need.
- [ ] Extend fixtures for several IDREFs, missing IDs, nested labels, programmatic focus, frames, late replies, and sensitive values. Provide deterministic transport cases in the lightweight test runner.

**Acceptance:** A human demonstrates correct browse-mode target matching, rapid target changes, Bridge off/disconnected/timeout, and unsupported pages. No response can enrich the wrong target, and native inspection remains available.

## Phase 3: Add Bounded Accessibility Checks and Contrast

**Suggested commit:** feat: add evidence-based element accessibility checks

**Files:** addon/globalPlugins/detailedElementInfo/audit.py (new); elementAnalyzer.py; Bridge/content.js for contrast metrics; scripts/run_tests.py; scripts/element_info_fixture.html; both user readmes.

**Proposed interface:** audit.evaluate(snapshot) returns a list of findings using the Phase 0 schema; it performs no NVDA reads, DOM queries, or network requests.

- [ ] Evaluate after native and available DOM data are joined. A missing required observation produces unknown; an excluded element produces not_applicable. warning means a heuristic or a finding needing human judgment, not incomplete proof disguised as fail.
- [ ] For controls requiring a name, evaluate the computed accessible name and applicable role. Empty-name failures require complete applicable evidence; source text alone cannot override an empty computed name.
- [ ] For images, account for decorative/presentational cases and valid alternative naming paths. Missing alt alone is not an automatic WCAG failure. Generic filenames and context-dependent alternative quality produce warnings.
- [ ] For form controls, account for wrapping labels, aria-label, resolved aria-labelledby, native button/input naming, and other applicable name sources. Distinguish missing accessible name from missing visible instructions/labels; do not equate a missing label-for pair with either failure.
- [ ] Add rule_id label_in_name for applicable controls: compare an established visible text label with the computed accessible name according to WCAG 2.5.3. A known incompatible name can fail; no visible text label is not_applicable; ambiguous label identification or incomplete name evidence is unknown. Cover W3C's case/punctuation examples and preserve meaningful symbols rather than applying an indiscriminate punctuation-removal rule.
- [ ] Present inherited language/direction, field constraints and group context, cell/header associations, and composite focus/selection as sourced diagnostic data. Do not infer a wrong natural language, invalid input, broken header mapping, or working keyboard navigation solely from attribute presence. New automatic failure rules beyond label_in_name require separately defined applicability and evidence.
- [ ] Treat observed non-semantic click behavior as a diagnostic warning until role and keyboard behavior are established. Do not require role=button for every clickable element or tabIndex=0 for every widget part. Do not claim exhaustive listener detection from inline attributes or onclick properties; delegated/framework listeners may be unobservable.
- [ ] Limit initial contrast checks to text with a reliably resolved uniform opaque foreground/background. Unsupported color spaces, alpha/compositing, background images/gradients, overlays, filters, or indeterminate backgrounds produce unknown rather than an invented white background. Conservative rejection is acceptable.
- [ ] For an 8-bit sRGB channel, normalize c = channel / 255; linearize to c / 12.92 when c <= 0.04045, otherwise ((c + 0.055) / 1.055) ** 2.4. Compute L = 0.2126 R + 0.7152 G + 0.0722 B from linear channels; ratio = (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05).
- [ ] Use 4.5:1 for ordinary text and 3:1 for qualifying large text: at least 18pt (24 CSS px), or 14pt (56/3 CSS px) when bold. Do not round ratios or threshold sizes before comparison. Treat unresolved font weight/size as unknown when it could change the result.
- [ ] Apply criterion 1.4.3 exclusions, including inactive controls, decoration, and logotypes where applicable. Checks are per inspected element, not an audit of the page or a claim of WCAG 2.1 AA compliance. Every fail names the relevant criterion and concrete evidence.
- [ ] Check black/white = 21:1, identical colors = 1:1, 4.499 fails the 4.5 threshold, large-text boundaries, and unsupported compositing. Native browser fixture checks must exercise the actual JavaScript calculation, not a separately reimplemented Python formula.
- [ ] Add false-positive fixtures for decorative images, alternative image names, wrapping labels, input submit names, roving tabIndex=-1, unavailable DOM, and truncated reference lists. The same facts must produce identical findings on repeated evaluation.
- [ ] Extend fixtures and focused checks for: visible Search/name Search site (pass), visible Search/name Run (fail), icon-only control (not_applicable), ambiguous label (unknown); inherited lang, explicit empty lang, overridden direction; grouped/wrapping labels and readonly validation inspection; missing/invalid form constraints; merged cells, explicit/missing headers, virtual row indices and unknown counts; composite DOM focus different from active descendant and selected state. Include capped/unsupported-scope observations and echoed sensitive validation text.

**Acceptance:** Deterministic cases pass for calculations, applicability, uncertainty, and false positives. Human review confirms the report clearly states its limited scope and does not present warnings as confirmed violations.

## Phase 4: Structure HTML and Export the Same Snapshot as Markdown

**Suggested commit:** feat: structure element reports and add Markdown export

**Files:** addon/globalPlugins/detailedElementInfo/config.py; settingsPanel.py; reportBuilder.py; __init__.py; scripts/run_tests.py; both user readmes.

- [ ] Add showAriaDetails, showLayoutAndContrast, showInteractivity, and showAccessibilityAudit, each defaulting to True only when the key is absent. Preserve existing field selections and all user values. Make Select all / Clear all consistent with the new section controls.
- [ ] Use an H1 report title and H2 sections for identity/roles, accessibility/ARIA, interaction/DOM, layout/appearance, diagnostic checks, ancestors, and technical attributes. Use H3 only for real subsections. Omit disabled/empty sections without hiding the provenance of displayed values.
- [ ] Display visible-label/name comparison, effective language and declaration source, form/group constraints, table coordinates/header names, and composite focus/active-descendant/selection in the existing relevant sections. Both serializers preserve provenance, unavailable states, and truncated context; no new setting or top-level UI panel is required.
- [ ] Adapt the existing HTML builder to consume the frozen snapshot. Escape untrusted content and use semantic lists or tables with text labels; status must never depend on color alone.
- [ ] Add the proposed ReportBuilder.buildMarkdownReport(snapshot) serializer. It uses the same visible fields, finding statuses, provenance, uncertainty, and truncation indicators as HTML, with appropriate Markdown escaping. Neither serializer recollects data.
- [ ] Add script_copyElementInfoMarkdown with proposed gesture kb:NVDA+control+shift+f1. Verify built-in/add-on gesture conflicts before registering the default; keep it remappable in Input Gestures. Use NVDA's verified clipboard API and announce success only after confirmed copy success.
- [ ] While an element report is open, copying uses that report's snapshot. From the page, the command captures one new target through the same collection path. No export path calls Gemini.
- [ ] Use native wx checkboxes and StaticText labels with logical Tab order. Self-audit accessible names, keyboard traversal, headings, and non-color status communication before presenting UI changes.
- [ ] Verify matching HTML/Markdown values under each section toggle, Select all / Clear all, empty data, escaped HTML/Markdown characters, and clipboard failure.
- [ ] Verify HTML/Markdown parity for all five context groups under the existing field/section choices. A native-only context value must remain distinguishable from a DOM-enriched value; exporting must not resolve additional references or change focus.

**Acceptance:** Human NVDA checks establish heading navigation, native settings accessibility, remappable gesture behavior, and truthful clipboard announcements. Export and displayed report refer to the same snapshot.

## Phase 5: Extend Explicit Gemini Analysis without Expanding Disclosure Implicitly

**Suggested commit:** feat: include bounded diagnostic evidence in Gemini analysis

**Files:** addon/globalPlugins/detailedElementInfo/ai_handler.py; __init__.py or reportBuilder.py only if needed to pass the snapshot; scripts/run_tests.py; both user readmes.

- [ ] Replace the assumption that dom_data already contains audit findings with an explicit adapter from the snapshot to a sanitized AI payload. Verify the existing analyze_dom_with_gemini entry point before changing its signature or callers.
- [ ] Keep transmission behind the existing explicit Alt+F1 action. Local reports, copying, settings changes, and audit evaluation must not send data. Disconnected/offline/error cases retain all local functions.
- [ ] Use an allowlist of identity/role, computed name/description, bounded relationship excerpts, applicable metrics, and diagnostic evidence. Exclude editable control values, password data, API keys, raw markup, and unrelated attributes; apply redaction to duplicated evidence and strings as well as named value fields.
- [ ] Limit the serialized AI payload to 16,000 characters. Drop optional excerpts/evidence entries deterministically until valid JSON fits; label omissions and never truncate a serialized JSON string into invalid data.
- [ ] Treat page text as untrusted evidence, never instructions. Preserve the existing requested-language behavior. Require two concise sections: Screen Reader Usage and Remediation Guide.
- [ ] Preserve unknown/not_applicable/warning distinctions. Gemini advice is advisory and must not turn incomplete evidence into certified WCAG findings. Escape returned text before HTML display.
- [ ] Verify the payload allowlist and caps with synthetic sensitive data; verify that report/copy paths make zero AI calls. Human testing of this optional path requires an explicit request and records failures without disclosing payloads or credentials.

**Acceptance:** Local behavior survives AI/network failure; a human explicitly exercises the changed Gemini path. Documentation identifies the new data categories and limits before release.

## Phase 6: Reconcile Documentation and Handoff State

**Suggested commit:** docs: document expanded element inspection and its limits

**Files:** readme.md; addon/doc/tr/readme.md; changelog.md; task.md; project_state.md.

- [ ] Check both readmes against the implemented sections, shortcut, new settings, source/availability labels, excerpt limits, contrast restrictions, and diagnostic status meanings. Features must not be advertised before they exist.
- [ ] Document the five context groups and their uncertainty: visible-label/name comparison, effective language/direction, form constraints/group context, table/header relationships, and composite focus/active-descendant/selection. Mark the separate observation extension below as deferred; do not describe event monitoring or actual speech capture as delivered.
- [ ] Explain native-only versus Bridge-enriched inspection, per-element scope, lack of whole-page conformance claims, explicit AI transmission, and retained offline behavior.
- [ ] Record actual completed milestones and pending human acceptance. Preserve original author details and version metadata; do not regenerate locale files or generated HTML manually.

**Acceptance:** English and Turkish cover the same behavior and limits; state files distinguish code written, deterministic checks, build outcome, and human acceptance.

## Phase 7: Verification and Human PR Handoff

**Suggested commit:** test: verify expanded element inspection scenarios

**Files:** scripts/run_tests.py; scripts/element_info_fixture.html; task.md; project_state.md; documentation only where verified behavior requires correction.

- [ ] Run the dependency-free scenario runner from the repository root: python scripts/run_tests.py. It must return a nonzero exit code for a failing scenario and report named cases and counts. Use only minimal NVDA stubs for pure logic; do not confuse stub results with screen-reader acceptance.
- [ ] Exercise the actual Bridge JavaScript against the retained HTML fixture in Chrome, including the contrast numeric and threshold cases. Record this separately from Python checks.
- [ ] Run the repository's existing configured lint/type checks; identify non-blocking checks explicitly. Run git diff --check and build with uv run scons using the documented tooling and gettext prerequisites. Do not add a test framework or replace project tooling.
- [ ] Have a human install the built add-on, or enable the Developer Scratchpad and copy the plugin to the configured NVDA profile, then restart/reload NVDA. Existing runtime-generated locale/build assets must remain build outputs.
- [ ] Test NVDA 2023.1 and 2026.1 separately, with at least one supported intervening release; record exact NVDA, Windows, browser, architecture, and Bridge versions. Untested combinations remain unverified, regardless of manifest values.
- [ ] In Chrome, verify semantic and custom controls, browse/focus modes, labels/relations, native-only mode, active Bridge, unsupported pages, frames, rapid target changes, timeout/reconnection, and detached targets. If no reliable cross-scope support exists, expect explicit unavailable/unknown results.
- [ ] Verify all diagnostic statuses, simple contrast success/failure and unsupported backgrounds, HTML/Markdown parity, heading navigation, settings Tab order and labels, gesture remapping, clipboard failure, redaction, and the explicitly requested Gemini success/error paths.
- [ ] Human acceptance must also cover the five context groups with the Phase 3 fixtures: visible-label/name differences; inherited/empty language and direction overrides; form/group constraints and validation messages without triggering validation; table headers/spans and virtual indices; composite DOM focus, active descendant, and selection. Confirm unchanged focus/input values and no broadened AI disclosure. These checks inspect current evidence and do not constitute implementation of the deferred observation extension.
- [ ] Verify native-only regression behavior in Firefox and in available supported non-IA2 contexts. No DOM-dependent check may silently pass when the Bridge cannot supply evidence.
- [ ] Record human results in project_state.md. Keep code-written, deterministic-checks-passed, build-succeeded, and human-accepted states distinct. Do not call the feature tested/working before human acceptance.
- [ ] Supply a human PR draft only after the relevant acceptance evidence exists; never open or push the PR. Suggested title: feat: expand element inspection and diagnostic reports. The body names actual delivered scope, environment, human results, limits, and any deferred work.

**Acceptance:** Required local checks and build have recorded outcomes, and a human has accepted the specified live scenarios. Missing human acceptance blocks a ready-for-PR claim.

## Deferred Extension: Observe Focus and Live Announcements

**Status:** deferred; not part of Phases 0-7 acceptance or the initial implementation. The user has authorized adding this extension to the plan, not implementing it. Before implementation, obtain review and approval of a separate bounded design, interfaces, and human acceptance scenarios.

**Purpose:** Help a human correlate actions with focus changes and live-region updates over time; a static element snapshot cannot establish those sequences.

- [ ] Propose an explicitly started/stopped local observation session. A prospective event record contains relative timestamp, event source, target identity, sanitized observed change, and availability; it is separate from the frozen inspection snapshot and never keeps raw editable/password values.
- [ ] Observe user-driven focus changes when opening/closing a dialog or moving through a widget, with expected start/end targets recorded by the tester. Record what occurred without automatically tabbing, opening/closing dialogs, submitting forms, or declaring all focus trapping incorrect; modal containment and an unwanted keyboard trap are different cases.
- [ ] Observe relevant DOM/accessibility events, live-region metadata, and bounded sanitized status changes when a user exercises success/error/loading scenarios. Distinguish a mutation or accessibility event from an NVDA announcement. A DOM event does not prove that NVDA spoke or that the user heard it; actual speech observation requires a separately verified NVDA mechanism or human confirmation.
- [ ] Define consent/start/stop controls, event filtering, finite duration/event/text limits, listener cleanup on stop/navigation/teardown, and event overflow behavior before implementation. No always-on logging, persistent transcript, or AI transmission by default. If actual speech capture is unsupported, report it unavailable and retain human confirmation.
- [ ] Specify deterministic event correlation/cleanup checks and human dialog/live-message scenarios. Record event-only evidence, observed NVDA output where verified, and human judgments separately; never infer end-to-end keyboard or announcement correctness from a synthetic event test.

**Non-goals:** This plan does not add a whole-page structure scan, zoom/reflow assessment, media-content evaluation, or whole-site WCAG certification. Those remain separate tester activities.

**Acceptance for this extension:** Approved design and explicit implementation authorization, bounded opt-in collection without unintended interaction/disclosure, verified listener cleanup, and human confirmation of the stated focus/announcement scenarios.

## Primary References

- [Core-AAM 1.1 Recommendation](https://www.w3.org/TR/core-aam-1.1/) and [Core-AAM 1.2 draft](https://www.w3.org/TR/core-aam-1.2/): distinguish standardized mappings, current draft additions, and actual browser/NVDA support.
- [Accessible Name and Description Computation](https://www.w3.org/TR/accname-1.2/): DOM excerpts do not implement accessible-name computation.
- [WCAG 2.1 contrast minimum](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html) and [compositing](https://www.w3.org/TR/compositing-1/): thresholds, linearization, exclusions, and supported visual scope.
- [ACT Rules Format](https://www.w3.org/TR/act-rules-format/) and [image-name rule](https://www.w3.org/WAI/standards-guidelines/act/rules/23a2a8/): applicability and evidence limits; the local warning vocabulary is diagnostic, not ACT certification.
- [Form labels](https://www.w3.org/WAI/tutorials/forms/labels/) and [APG keyboard interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/): naming paths, roving tabindex, and keyboard behavior.
- [NVDA 2026.1 changes](https://api.nvaccess.org/releases/2026.1/documentation/en/changes.html): API/architecture transition; compatibility must be verified on the stated versions.
- [Label in Name](https://www.w3.org/WAI/WCAG21/Understanding/label-in-name.html): visible text-label comparison, applicability, and interpretation limits.
- [Language declaration and inheritance](https://www.w3.org/International/questions/qa-html-language-declarations) and [Language of Parts](https://www.w3.org/WAI/WCAG21/Understanding/language-of-parts.html): effective language is distinct from direction and pronunciation observations.
- [Form grouping](https://www.w3.org/WAI/tutorials/forms/grouping/) and [validation](https://www.w3.org/WAI/tutorials/forms/validation/): contextual instructions and input/validation evidence.
- [Grid/table properties](https://www.w3.org/WAI/ARIA/apg/practices/grid-and-table-properties/) and [irregular headers](https://www.w3.org/WAI/tutorials/tables/irregular/): indices, spans, virtualized data, and header relationships.
- [Focus order](https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html), [modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/), and [status messages](https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html): temporal observation and human testing; APG pattern advice is not itself a list of independent WCAG failures.
