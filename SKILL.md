---
name: detailed-element-info
description: Maintain and locally verify the Detailed Element Info NVDA add-on and Chrome Bridge.
---

# Development workflow

Read AGENTS.md, plan.md, task.md and project_state.md before changing behavior. Runtime code uses only the Python standard library and NVDA APIs, and must support Python 3.7 / NVDA 2023.1. Preserve version metadata, locale sources and existing user settings.

Keep task.md, project_state.md and changelog.md current. Review each milestone before advancing. Do not push or open pull requests.

## Local checks

- Run the dependency-free scenarios with `python scripts/run_tests.py`.
- Run actual Bridge source checks with `node scripts/test_bridge_js.js`.
- Optional actual Chrome checks: `python scripts/run_tests.py --browser`. This uses the developer's installed Playwright and Chrome; the add-on never imports Playwright. Optional verification dependencies are listed in requirements.txt.
- Run repository Ruff/Pyright checks through the existing uv environment and build with `uv run --no-sync scons`. Record existing failures separately; a successful package build is not screen-reader acceptance.
- Keep scripts/element_info_fixture.html as a source fixture despite the generic HTML ignore rule. It contains deliberate negative accessibility cases.

## Snapshot and Bridge contract

Capture the NVDA target once on the UI thread. Render or export frozen plain data; never re-read the current target from a serializer.

Bridge requires available native application_name == chrome and windows.get focused === true. Window-focus changes cancel the pending request and clear all witnesses, including pre-capture witnesses from another Chrome window. Until a fresh content-script heartbeat precedes capture, return native-only. Firefox/unknown applications never request Bridge.

Bridge uses a pre-capture browser witness, prepare/ready, server /bind, pinned document collection, then /update. Missing identity, witness, supported scope or deadline yields native-only output. The browser document/activation binding does not prove that NVDA's provider cache is current. A verified accepted DOM result freezes a historical snapshot; later navigation does not change its identity. A newer inspection generation invalidates queued callbacks.

Apply a shared limit of eight reference targets, 500 characters per excerpt and 4000 combined. Native provider prefetch is outside Python consumer control. Preserve native and DOM observations separately. Private editable text, protected markup and unsafe validation-message echoes do not enter new DOM outputs. Framework event summaries are bounded untrusted hints.

## Local audit contract

audit.evaluate(snapshot) is pure and returns per-element findings only. Missing evidence is unknown; warnings require human judgment. Do not infer absent visible labels from absent programmatic association. Preserve meaningful math and use unknown for symbolic ambiguity. Contrast only accepts bounded uniform opaque direct text; unhandled paint or background returns unknown. None of these findings establishes page-level WCAG conformance.

## Reports and copying

ReportBuilder.buildReport(snapshot) and buildMarkdownReport(snapshot) accept frozen dictionaries only. The optional analyzer constructor argument is retained for compatibility and never used. Capture derived facts and ancestor snapshots before rendering. Freeze FIELD_OPTIONS in availability.report_fields; bulk native checkbox selection includes the four new sections.

Markdown copy is unbound by default; NVDA+Ctrl+Shift+F1 conflicts with NVDA. The shared capture callback handles page reports/copy. Modeless report UUID captions plus NVDA process identity select a frozen cache entry; never use global latest data. Cache size is 20; eviction gives unavailable. Clipboard success requires api.copyToClip(..., notify=False) is True.

## Explicit Gemini contract

Only explicit Alt+F1 from an owned element report analyzes that frozen snapshot. server.get_ai_analysis requires an explicit snapshot; no-argument use never transmits latest DOM. build_ai_payload selects tag/role, safe computed name/description, bounded relation excerpts, selected contrast metrics and rule/status evidence. No raw values/markup/URLs/selectors/handles/attributes or five new context groups. Redact known captured values and key duplicates. Fail closed for protected/uncertain text and for editable optional text without usable value evidence; omit editable relationship excerpts. The valid JSON payload and complete request body stay within 16000 characters. Drop optional whole items, record omissions, preserve locale/status uncertainty and escape returned text.

Use only stdlib HTTP with 15-second timeout, key in x-goog-api-key header and private-safe error categories/status. Never run live Gemini in local checks. Saving Advanced Support starts/stops the existing local Bridge server. Queued AI output respects plugin lifetime and capture/AI generations.

## Human acceptance

Do not launch NVDA or claim screen-reader behavior is tested/working/done. Human checks on supported NVDA versions, heading navigation, native settings, clipboard behavior and explicit Gemini requests remain separate acceptance gates. No automated check may send data to Gemini.
