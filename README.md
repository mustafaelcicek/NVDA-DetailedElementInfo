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
- **Advanced Chrome Bridge (Experimental)**: Connects directly to a custom Chrome extension to fetch raw DOM elements, active properties, and HTML attributes instantly.

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

## Technical Details

This add-on utilizes a **Zero-Dependency Native Architecture**:
- Pure Python standard libraries (`http.server`, `urllib.request`) to avoid `pip` dependency hell and OpenSSL issues.
- IAccessible2 (IA2) interfaces for accessibility attributes.
- NVDA's object model and control types.
- WAI-ARIA 1.2 specifications and Windows MSAA roles.
- **HTTP Long Polling**: A custom, lightweight communication bridge with Chrome's Manifest V3 service workers, kept alive by content-script heartbeats.

## Author

Mustafa Elçiçek <mustafaelcicek5656@gmail.com>

## Supported NVDA Versions

- Minimum: NVDA 2023.1
- Last tested: NVDA 2026.1

## License

GPL-2.0

## Contributing

Contributions are welcome! Please report bugs and suggest improvements.

## Contributors

- **Uğur Gürbüz** — Thank you for your valuable support and thoughtful ideas.
- **Google Gemini ve GitHub Copilot** — Although I don't have coding knowledge to develop an NVDA add-on, I thank these AI assistants for guiding me throughout the process, from writing code to resolving errors, until the idea became a working add-on.

## Changelog

Please see the [CHANGELOG.md](CHANGELOG.md) file for a detailed history of updates and architectural improvements.
