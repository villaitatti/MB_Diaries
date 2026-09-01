# Transcription fixes — 1895-96

Source: `assets/input/1895-96/1895-96.docx`

**1** fixes applied · **2** reviewed, no fix needed

## Fixes applied

### `1895-96-01` — missing space after closing quote before capital letter

```diff
- strangers -”Bernhard began
+ strangers -” Bernhard began
```

## Reviewed, no fix needed

- **p.214, 450, 568, 570, 927, 930, 982, 985, 1053, 1211** — all 10 of these Category B matches are the surname "Hildebrand" (the sculptor Adolf von Hildebrand and his family), which the scanner's `"and"` word-glue suffix matches as a false positive. Real proper noun, not glued text.
- **p.1243** `"Violet in Wonderland"` — same `"and"` suffix false positive; a real word/title reference (Alice in Wonderland-style pun used by the diarist for a story title), not glued text.

---
Generated from: `transcription_fixes_changelog.md`
