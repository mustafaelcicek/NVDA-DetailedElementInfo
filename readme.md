# Detailed Element Info

A powerful NVDA add-on that provides detailed accessibility information about HTML elements on web pages.

## Overview

Detailed Element Info is a utility add-on for NVDA that allows you to inspect HTML elements and view their accessibility attributes, ARIA roles, and semantic information. This is particularly useful for web developers, accessibility auditors, and NVDA users who want to understand how screen readers perceive web content.

## Features

- **Display ARIA Roles**: See the computed ARIA role of any HTML element
- **Show Accessible Names**: View the accessible name and its source (aria-label, alt text, content, etc.)
- **Detect Semantic Mismatches**: Identify when explicit ARIA roles conflict with native HTML semantics
- **Inspect Attributes**: View all IA2 attributes and ARIA properties
- **Show DOM Path**: See a concise DOM path for the focused element
- **Captured Ancestors**: View parent-element information within the frozen report
- **Captured States**: View element states (expanded, checked, selected, etc.) as ARIA attributes; this does not observe later changes
- **Source Detection**: Understand where accessible names come from (aria-label, contents, alt, title, etc.)
- **Name Source Confidence**: See how certain the add-on is about where the accessible name comes from (certain, inferred, unknown)
- **Multiple Role Views**: Compare the explicit ARIA role, native HTML role, NVDA role, and the final inferred role side by side
- **MSAA Role & Heading Level**: View the raw MSAA role and, for headings, the heading level
- **Derived State Attributes**: See ARIA-like attributes derived from NVDA states (expanded, checked, selected, etc.)
- **Configurable Fields**: Choose exactly which fields appear in the report from the add-on settings, with Select all / Clear all
- **Advanced Support — Chrome Bridge (Experimental)**: Connect to a companion Chrome extension to fetch the page's real DOM data, HTML attributes, and active properties directly
- **AI Analysis with Gemini (Experimental)**: Ask Google Gemini for a plain-language explanation of what the focused element is and how it can be used

## Installation

Install the matching .nvda-addon package through NVDA's add-on installation dialog and restart NVDA. For DOM enrichment, also install the matching Chrome Bridge as described below. Native inspection, local checks and copying do not require Gemini.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| NVDA+Shift+F1 | Show focused element details |
| Alt+F1 | Analyze the reported element with AI while the report is open |
| Unassigned | Copy focused element information as Markdown; assign in Input Gestures |

> Assign or change commands in **Preferences > Input Gestures** in NVDA.

## How to Use

1. Navigate to any HTML element on a web page using Tab key or arrow keys
2. Press NVDA+Shift+F1 to show focused element details
3. A browseable message window will open showing:
   - Element tag name and attribute count
   - Accessible name and its source
   - Computed ARIA role
   - Native vs. explicit role source
   - Semantic mismatches
   - All raw IA2 attributes
   - DOM path of the focused element
   - Parent elements up the DOM tree
4. With Advanced Support enabled, press Alt+F1 while the report is open to request an AI analysis.


## Information Displayed

### Accessible Name
The name that screen readers announce for the element.

### Name Source
Where the accessible name comes from:
- **aria-label**: Explicit ARIA label
- **aria-labelledby**: Reference to another element
- **contents**: Text content of the element
- **alt**: Alt text (for images)
- **value**: Element value attribute
- **title**: Title attribute
- **placeholder**: Placeholder text

### Computed Role
The ARIA role determined from:
1. Explicit XML-roles (role attribute)
2. HTML native semantics
3. NVDA control type mapping
4. Unknown (fallback)

### Semantic Source
Whether the role comes from:
- **native HTML**: HTML's implicit semantics (e.g., <button> → button role)
- **explicit role**: role attribute override
- **redundant explicit role**: role attribute matches native semantics
- **unknown**: Unable to determine

### Native Semantic Mismatch
Indicates whether an explicit ARIA role conflicts with the element's native HTML semantics.

### DOM Path
A compact technical path that helps identify the element location in the page structure (for example: `main > form#login > input[name="email"]`).

## Frozen reports and Markdown

HTML and Markdown use the same captured facts and field choices, with H1/H2 headings, provenance, availability and partial/truncated evidence. Native and DOM observations stay separate. Checks concern one element and do not establish page-level WCAG conformance.

Assign **Copy focused element information as Markdown** in Input Gestures. It is unassigned by default because NVDA+Ctrl+Shift+F1 already belongs to NVDA. From an open report it copies that report's frozen snapshot; from the page it captures one new target. Clipboard failure and unavailable old snapshots are announced explicitly. Neither path calls Gemini.

Four native section settings default on only when absent: **Accessibility and ARIA**, **Layout and contrast**, **Interaction and DOM**, and **Diagnostic checks**. Existing choices are preserved; Select all / Clear all includes them. Human NVDA acceptance remains pending.

## Settings

Open **NVDA menu > Preferences > Settings > Detailed Element Info** to configure the add-on:

- **Choose which fields to show**: Toggle each field of the report on or off — tag summary, accessible name, name source and confidence, DOM tag and path, explicit / native / NVDA / final roles, semantic source and mismatch, raw IA2 attributes, attributes derived from NVDA states, MSAA role, and ancestor elements.
- **Select all / Clear all**: Turn every field on or off at once.
- **Enable Advanced Support (AI and Chrome extension)**: Turns on the experimental Chrome Bridge and AI features described below.
- **Gemini API Key**: Enter your own Google Gemini API key so the AI analysis can run.

## Advanced Support — Chrome Bridge (Experimental)

Detailed Element Info can optionally connect to a companion Chrome extension to look beyond NVDA's virtual buffer and read the page's real DOM.

- When Advanced Support is enabled, the add-on starts a local server at `127.0.0.1:63333` and requests element data from the Chrome extension.
- DOM enrichment requires a captured Chrome application and a focused Chrome window. Firefox, other browsers and unknown application identity retain native evidence. A window-focus change cancels pending capture and clears prior witnesses; capture can fall back to native evidence until the next content-script heartbeat.
- Bridge capture now requires a previously witnessed top-level document and a pinned handshake; uncertain identity, unsupported frames or timeout retain native information.
- Capture records bounded labels, language/direction, form/group, table and composite context with separate native/DOM sources. Protected or uncertain protection omits DOM text/markup/context. Editable text and validation-message echoes are excluded; reference summaries share eight targets and 4000 characters.
- Local capture checks and independent review have passed. Human NVDA acceptance remains pending. Pure local checks for computed names, image alternatives, label-in-name, click diagnostics and conservative direct-text contrast are written; the structured HTML/Markdown presentation and per-report copy are written and locally checked. These checks do not certify a page or establish overall WCAG conformance.
- See the [cumulative changelog](changelog.md) for the local implementation status.
- Download `detailedElementInfo-chrome-bridge.zip` from the matching GitHub release and extract it. Then open `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**, and select the extracted `Bridge` folder.
- The extension runs on web pages so it can inspect the matched element. Browser-internal pages such as `chrome://` pages cannot be inspected.
- This feature is experimental and under active development; live correlation, matching boundaries, and security filters are being hardened.

## AI Analysis with Gemini (Experimental)

With Advanced Support enabled and your own Gemini API key configured, press **Alt+F1** in an element report to request analysis of that report's frozen snapshot. Opening reports, copying Markdown, changing settings and local checks make no Gemini requests.

The allowlist contains the element tag/role, sanitized computed name/description when safe, bounded relationship excerpts, selected contrast metrics and diagnostic rule/status evidence. It excludes editable values, protected data, raw markup, URLs, selectors, window handles, unrelated attributes and the five new context groups. Known sensitive values and the configured key are redacted if duplicated in allowed text. Optional text is omitted when protection is uncertain or an editable target lacks usable value evidence. The valid JSON payload is capped at 16,000 characters; optional entries may be dropped with omission reasons.

This still transmits selected text to Google: request analysis only for content you intend to send. Page text is untrusted evidence. The prompt requests **Screen Reader Usage** and **Remediation Guide** in NVDA's language; returned advice is escaped for display and remains advisory. Errors reveal only a category or HTTP status, without credentials or response bodies. Offline/API failures leave local reports and copying available.

The configured model remains `gemini-2.5-flash`. Google currently [limits access to 2.5 models to existing users](https://ai.google.dev/gemini-api/docs/deprecations#gemini-2.5-flash-models); an account without access may receive an API error. No live Gemini acceptance has been performed for this expansion.

## Technical Details

This add-on utilizes a **zero-dependency native architecture**:
- Pure Python standard libraries (`http.server`, `urllib.request`) to avoid `pip` dependency issues.
- IAccessible2 (IA2) interfaces for accessibility attributes
- NVDA's object model and control types
- WAI-ARIA 1.2 specifications
- Windows MSAA roles
- **HTTP long polling**: a lightweight bridge to the companion Chrome extension's Manifest V3 service worker, kept alive by content-script heartbeats.

## Developer build

There is no runtime CLI; use NVDA's commands and settings. Build from a checkout with the tools declared in [pyproject.toml](pyproject.toml):

```text
uv run --no-sync scons
```

See the [development workflow](SKILL.md), [configuration schema](addon/globalPlugins/detailedElementInfo/config.py), and [cumulative changelog](changelog.md). Generated help and packages are build outputs.

Focus-transition and live-announcement observation remain deferred; the report records current evidence only.

## Author

Mustafa Elçiçek <mustafaelcicek5656@gmail.com>

## Implementation contributor

- Kamal Yaser
- Email: [kamalyaser31@gmail.com](mailto:kamalyaser31@gmail.com)
- Telegram: [@kamalyaser31](https://t.me/kamalyaser31)

## Supported NVDA Versions

- Minimum: NVDA 2023.1
- Upstream documentation reports NVDA 2026.1; this expansion still requires human checks on 2023.1, an intervening release and 2026.1.

## License

GPL-2.0

## Contributing

Contributions are welcome! Please read the [Contributing Guide](CONTRIBUTING.md) in the project repository before reporting bugs, suggesting improvements, or opening a pull request.

## Contributors

Detailed Element Info is built with the help of code contributors, testers, and supporters. For the full list of contributors and what each of them worked on, see [CONTRIBUTORS.md](CONTRIBUTORS.md) in the project repository.

## Changelog

### Version 1.1.0
- Added a packaged Manifest V3 Chrome Bridge for retrieving live DOM data.
- Added on-demand Google Gemini analysis with Alt+F1 and locale-aware responses.
- Improved focused-element matching between NVDA and Chrome.
- Completed the Ukrainian localization and corrected mixed-language Turkish and Ukrainian output.
- Restricted Bridge requests to Chrome-extension origins, redacted password values, and escaped AI output.
- Added a separate Chrome Bridge ZIP to tagged GitHub releases.

### Version 1.0.2
- Migrated the project to the NV Access add-on template and SCons build system.
- Automated manifest, translation, documentation, and add-on package generation.

### Version 1.0.1 (NVDA 2026.1 Compatibility)
- Updated add-on compatibility metadata for NVDA 2026.1

### Version 1.0.0 (Initial Release)
- Initial release of Detailed Element Info
- Display ARIA roles and attributes
- Show accessible names and sources
- Detect semantic mismatches
- Parent element navigation
