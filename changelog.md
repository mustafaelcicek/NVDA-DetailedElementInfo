# Changelog

All notable changes to this project will be documented in this file.

## [1.0.2]

### Added
- **Chrome Bridge (Advanced Support):** Added a dedicated companion Chrome extension (Bridge) for the add-on, letting NVDA access the page's real DOM data, HTML structure, and live properties directly, instead of being limited to the browser's virtual buffer.
- **AI (Gemini) Analysis:** Added Google Gemini analysis of the collected raw DOM data and ARIA attributes (runs once the DOM data has been retrieved).
- **Chrome Extension Communication:** Set up a local communication server in the background using `http.server` and `urllib.request`.
- **Structured HTML Reporting:** Report output moved from plain text to a hierarchical HTML interface (Browseable Message) with clean headings (H1, H2) and structured lists.
- **Settings Panel Update:** Added "Enable Advanced Support" and "Gemini API Key" options to the NVDA add-on settings.

### Changed
- The reporting interface was enriched to show both NVDA's standard IA2 data and the deeper analysis from Chrome and AI.
