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
- **Parent Navigation**: Navigate through parent elements to understand document structure
- **State Tracking**: View element states (expanded, checked, selected, etc.) as ARIA attributes
- **Source Detection**: Understand where accessible names come from (aria-label, contents, alt, title, etc.)
- **Name Source Confidence**: See how certain the add-on is about where the accessible name comes from (certain, inferred, unknown)
- **Multiple Role Views**: Compare the explicit ARIA role, native HTML role, NVDA role, and the final inferred role side by side
- **MSAA Role & Heading Level**: View the raw MSAA role and, for headings, the heading level
- **Derived State Attributes**: See ARIA-like attributes derived from NVDA states (expanded, checked, selected, etc.)
- **Configurable Fields**: Choose exactly which fields appear in the report from the add-on settings, with Select all / Clear all
- **Advanced Support — Chrome Bridge (Experimental)**: Connect to a companion Chrome extension to fetch the page's real DOM data, HTML attributes, and active properties directly
- **AI Analysis with Gemini (Experimental)**: Ask Google Gemini for a plain-language explanation of what the focused element is and how it can be used

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| NVDA+Shift+F1 | Show focused element details |

> Note: You can change this shortcut from **Preferences > Input Gestures** in NVDA.

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

## Settings

Open **NVDA menu > Preferences > Settings > Detailed Element Info** to configure the add-on:

- **Choose which fields to show**: Toggle each field of the report on or off — tag summary, accessible name, name source and confidence, DOM tag and path, explicit / native / NVDA / final roles, semantic source and mismatch, raw IA2 attributes, attributes derived from NVDA states, MSAA role, and ancestor elements.
- **Select all / Clear all**: Turn every field on or off at once.
- **Enable Advanced Support (AI and Chrome extension)**: Turns on the experimental Chrome Bridge and AI features described below.
- **Gemini AI Token**: Enter your own Google Gemini API key so the AI analysis can run.

## Advanced Support — Chrome Bridge (Experimental)

Detailed Element Info can optionally connect to a companion Chrome extension to look beyond NVDA's virtual buffer and read the page's real DOM.

- When Advanced Support is enabled, the add-on starts a lightweight local server (`127.0.0.1:63333`) that talks to the Chrome extension using HTTP long polling.
- The report then includes an **Active element's DOM attributes** section with the live HTML attributes and properties fetched from Chrome.
- This requires the companion Chrome extension to be installed. The feature is experimental and under active development.

## AI Analysis with Gemini (Experimental)

With Advanced Support enabled and a Gemini API token set, the report offers a **Request AI comment** action.

- The collected DOM data is sent to Google Gemini, which returns a short, plain-language explanation of what the element is, its purpose, and how a screen reader user can interact with it.
- This requires your own Google Gemini API key, entered in the settings. The feature is experimental.

## Technical Details

This add-on utilizes a **zero-dependency native architecture**:
- Pure Python standard libraries (`http.server`, `urllib.request`) to avoid `pip` dependency issues.
- IAccessible2 (IA2) interfaces for accessibility attributes
- NVDA's object model and control types
- WAI-ARIA 1.2 specifications
- Windows MSAA roles
- **HTTP long polling**: a lightweight bridge to the companion Chrome extension's Manifest V3 service worker, kept alive by content-script heartbeats.

## Author

Mustafa Elçiçek <mustafaelcicek5656@gmail.com>

## Supported NVDA Versions

- Minimum: NVDA 2023.1
- Last tested: NVDA 2026.1

## License

GPL-2.0

## Contributing

Contributions are welcome! Please read the Contributing Guide (`CONTRIBUTING.md`) in the project repository before reporting bugs, suggesting improvements, or opening a pull request.

## Contributors

Detailed Element Info is built with the help of code contributors, testers, and supporters. For the full list of contributors and what each of them worked on, see `CONTRIBUTORS.md` in the project repository.

## Changelog

### Version 1.0.2
- Added an experimental Chrome Bridge companion extension so the add-on can read the page's real DOM data instead of relying only on NVDA's virtual buffer.
- Added experimental AI analysis of the collected DOM/ARIA data using Google Gemini.
- Reports are now shown in a structured, hierarchical HTML view instead of plain text.
- Added "Enable Advanced Support" and "Gemini API Key" options to the add-on settings.

### Version 1.0.1 (NVDA 2026.1 Compatibility)
- Updated add-on compatibility metadata for NVDA 2026.1

### Version 1.0.0 (Initial Release)
- Initial release of Detailed Element Info
- Display ARIA roles and attributes
- Show accessible names and sources
- Detect semantic mismatches
- Parent element navigation

