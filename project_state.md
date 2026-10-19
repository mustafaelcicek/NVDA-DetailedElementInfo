# Project State
Updated: 2026-10-19

## Current checkpoint
Approved Phases 0-7 remain active. The user chose direct root repair after Antigravity's initial Phase 2 and Phase 2A repair failed independent review. Root repaired the evidenced defects and independent review found no new direct Phase 2 regression. Phase 3 is locally verified after independent review; Phase 4 is in progress. Phases 5-7 and human NVDA acceptance remain pending. Native milestone e928a6d is committed; subsequent work is uncommitted on feat/expanded-element-info. No push or PR.

## Implemented capture contract
- One native target capture on UI thread; guarded getters, provenance and explicit availability preserve empty/false/zero.
- Strict prior browser witness and pinned prepare/bind/collect/update handshake, exact document/frame/nonce identity, finite deadlines and generation cancellation. Missing reliable identity yields native-only with reason. A verified accepted result freezes historical facts.
- Pagehide/pageshow invalidate activation; sender metadata required. Framework events are bounded untrusted advisory names.
- Protected/indeterminate DOM text, markup, references and context omitted; legacy raw chrome_data cannot bypass sanitized HTML.
- Shared native/DOM reference budget: 8 targets, 500 characters per excerpt, 4000 combined. High-level provider prefetch cannot be bounded by Python slicing; no invented API arguments.
- Native header text preserved; DOM and native context stay separate. Bounded visible labels, language/direction, forms/groups, table spans/virtual indices and composite focus/selection. Editable descendants and validation echoes excluded. Overlapping marker ownership restores the original marker.

## Evidence and limits
Default runner: 54/54. Optional actual Chrome 147.0.7727.138: 37/37 after direct repair and formatting. Real production JS and actual server/plugin callback paths exercised with external API boundaries replaced; these checks are not NVDA acceptance. No Google requests.
Targeted Python 3.7 audit/server/snapshot: 0 errors/0 warnings. Black and flake8 pass on six touched Python files. SCons build succeeds; final package must be rebuilt after later phases. Full Pyright has 1816 errors over 13 actual files (original baseline 726); unresolved, not all attributable to NVDA stubs. The 29 audit.py reports ask for post-3.7 typing syntax because the global default targets build-tool Python; audit.py is clean at Python 3.7. .tmp backups excluded from typing analysis. Final build/gates pending.

## Decisions for continuation
- Runtime Python 3.7 / NVDA 2023.1 floor; stdlib + NVDA only. Playwright in requirements.txt is optional developer browser verification, never bundled.
- Snapshot sections: target/native/aria/dom/layout/context/audit/availability; renderers/AI consume frozen facts only.
- Four future section booleans default true only if absent; preserve user values.
- Markdown copy remains unbound by default: proposed NVDA+Ctrl+Shift+F1 conflicts with NVDA log-fragment command. Announce only successful api.copyToClip. Several modeless reports require separate frozen identities.
- AI only explicit Alt+F1; allowlist, duplicate-sensitive-text redaction and 16000-character valid JSON cap; new context never implicitly expands disclosure.
- Observation extension deferred. Preserve version, buildVars.py, locales and existing settings.
- Force-add scripts/element_info_fixture.html when committing; generic *.html ignore otherwise hides it.

## Next step
Implement pure HTML/Markdown/settings/copy, then explicit sanitized Gemini, bilingual docs and final local verification. Phase 3 findings retain source/evidence and limited applicability: unestablished visible-label associations remain unknown; ambiguous mathematical labels remain unknown. Contrast supports only bounded uniform direct text with opaque sRGB and rejects unresolved paint, overlays, shadows, generated content, filters and content-visibility. Per-element findings never certify a page. Human screen-reader acceptance is a separate release gate.
