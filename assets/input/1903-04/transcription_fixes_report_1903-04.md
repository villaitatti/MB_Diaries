# Transcription fixes — 1903-04

Source: `assets/input/1903-04/1903-04.docx`

**2** fixes applied · **2** reviewed, no fix needed

## Fixes applied

### `1903-04-01` — missing space before page marker [183] glued inside Brookline

```diff
- Brook[183] line
+ Brook [183] line
```

### `1903-04-02` — missing space before page marker [199]

```diff
- a.m.[199]
+ a.m. [199]
```

## Reviewed, no fix needed

- **p.112** "Bourland", **p.303**/**p.305** "Marquand" (x4, a real surname, the Marquand family), **p.408** "washstand", "shorthand", **p.429** "beforehand", **p.459**/**p.462**/**p.536**/**p.541** "Cleveland" (x5) — all Category B word-glue false positives: every one is a single real word or proper noun/place name ending in "-land"/"-and". No fix needed.
- **p.299** "Wednesday Dec. 2. [190]3" and **p.302** "Friday Dec. 4. [190]3." — the `[190]` bracket is the diarist/editor's inline year-correction annotation completing the year as "1903" (the same convention as `[1903]` in 1902-03), not a missing space around a page marker. Left as-is.

---
Generated from: `transcription_fixes_changelog.md`
