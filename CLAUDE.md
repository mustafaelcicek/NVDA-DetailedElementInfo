# Claude Code Instructions

Project-specific guidance for Claude Code. See `AGENTS.md` for the full agent standards
and `CONTRIBUTING.md` for the contributor guide; the key points are repeated here.

**Detailed Element Info** is an NVDA screen-reader add-on (Python) that reports
accessibility, ARIA, and DOM details for the focused HTML element. Add-on code is under
`globalPlugins/detailedElementInfo/`.

Rules:

- Standard library and NVDA APIs only — **no third-party / `pip` dependencies**. Keep
  NVDA 2023.1+ compatibility.
- Keep strings translatable (`_()`) and update `doc/en/` and `doc/tr/` (`.md` + `.html`)
  when features change. Don't touch version numbers, `manifest.ini`, or locale files
  unless asked.
- You cannot run NVDA — **never claim a change is tested or working**; say it still needs
  manual human testing in NVDA.
- You may commit (follow the commit-message rules in `CONTRIBUTING.md`), but **do not add
  a `Co-Authored-By: Claude` trailer** and **do not open pull requests**. If asked for a
  PR, hand over a draft (title + description) for a human to test and open.
