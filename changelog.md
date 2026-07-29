# Changelog

All notable changes to this project will be documented in this file.

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
