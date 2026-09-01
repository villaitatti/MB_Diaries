# Transcription fixes — 1894-95

Source: `assets/input/1894-95/1894-95.docx`

**3** fixes applied · **5** reviewed, no fix needed

## Fixes applied

### `1894-95-01` — missing space after closing quote before capital letter

```diff
- in a bowl!”Another Baptist
+ in a bowl!” Another Baptist
```

### `1894-95-02` — missing space after colon in date header

```diff
- 1894. :Hotel de France
+ 1894. : Hotel de France
```

### `1894-95-03` — missing space before page marker [090]

```diff
- Fin du Paganism.[090]
+ Fin du Paganism. [090]
```

## Reviewed, no fix needed

- **p.45** `their “occasional publication”, the ”Dial”. Its illustrations` — the scanner flags `”D` (a closing curly quote directly followed by a capital letter) here, but there is no missing whitespace: the opening quote before "Dial" was simply typed with the wrong curly-quote direction (`”` instead of `“`). Both sides of the word already have proper spacing, so this isn't the glued-text bug this pass is fixing; left untouched.
- **p.158** (×4), **p.750**, **p.406-style** `Hildebrand` matches — the scanner's word-glue suffix list includes `"and"`, which also matches the tail of the sculptor's surname "Hildebrand". Real word/proper noun, not a glue bug.
- **p.708** `Newfoundland dog` — same `"and"` suffix false positive; real word.
- **p.816** `Bernhard overcame Janet's objection` — matches the `"came"` suffix; real word "overcame", not glued text.
- **p.1017** `nothing about beforehand` — matches the `"and"` suffix; real word "beforehand", not glued text.

---
Generated from: `transcription_fixes_changelog.md`
