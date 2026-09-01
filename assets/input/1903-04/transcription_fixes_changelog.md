# Transcription fix log — 1903-04.docx

Generated: 2026-09-01T10:11:17.930095+00:00
Fixes definition: `assets/scripts/fixes/1903-04_fixes.json`

## Applied (2)

- **1903-04-01** — missing space before page marker [183] glued inside Brookline
  - `Brook[183] line` → `Brook [183] line`
- **1903-04-02** — missing space before page marker [199]
  - `a.m.[199]` → `a.m. [199]`

## Skipped / needs manual review (0)

## Reviewed, no fix needed

- **p.112** "Bourland", **p.303**/**p.305** "Marquand" (x4, a real surname,
  the Marquand family), **p.408** "washstand", "shorthand", **p.429**
  "beforehand", **p.459**/**p.462**/**p.536**/**p.541** "Cleveland" (x5) —
  all Category B word-glue false positives: every one is a single real
  word or proper noun/place name ending in "-land"/"-and". No fix needed.
- **p.299** "Wednesday Dec. 2. [190]3" and **p.302** "Friday Dec. 4. [190]3."
  — the `[190]` bracket is the diarist/editor's inline year-correction
  annotation completing the year as "1903" (the same convention as `[1903]`
  in 1902-03), not a missing space around a page marker. Left as-is.

