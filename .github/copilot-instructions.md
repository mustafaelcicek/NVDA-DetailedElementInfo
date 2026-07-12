# GitHub Copilot Instructions

**Detailed Element Info** is an NVDA screen-reader add-on written in Python that reports
accessibility, ARIA, and DOM details for the focused HTML element. Add-on code lives in
`globalPlugins/detailedElementInfo/`. See `AGENTS.md` and `CONTRIBUTING.md` for full
details.

When suggesting code or changes:

- Use only the Python standard library and NVDA's own APIs — **no third-party / `pip`
  dependencies**. Maintain compatibility with NVDA 2023.1 and newer.
- Match the existing style in `globalPlugins/detailedElementInfo/`.
- Keep user-facing strings translatable with `_()`, and update `doc/en/` and `doc/tr/`
  (both `readme.md` and `readme.html`) when a feature changes.
- Don't change version numbers, `manifest.ini`, or locale files unless asked.
- Every change must be manually tested in NVDA by a human before it ships — automated
  checks are not enough.
- Follow the commit-message guidelines in `CONTRIBUTING.md`, and don't add AI co-author
  trailers to commits.
