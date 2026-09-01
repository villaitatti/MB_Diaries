# Transcription fixes — 1906

Source: `assets/input/1906/1906.docx`

**1** fixes applied · **3** reviewed, no fix needed

## Fixes applied

### `1906-01` — missing space after closing parenthesis and period before capitalized word

```diff
- church).Then to San Valentino
+ church). Then to San Valentino
```

## Reviewed, no fix needed

- **p.63, p.108** "Bernhad reading..." / "Bernhad dined with..." — the scanner flagged "Bernhad" as a "Bern"+"had" word-glue compound, but it is a transcription typo (missing "r") for "Bernhard", not two words run together with no whitespace. Out of scope for this glue-fix pass; left as-is (appears 2x vs. 69x correctly as "Bernhard" elsewhere).
- **p.216, p.221** "Cleveland" — real place name/proper noun ("Cleveland pictures"), not "Clever"+"land" glued. False positive.
- **p.807, p.1115, p.1136** "Rowland" (Mrs. Rowland) — real surname, not "Row"+"land" glued. False positive.

---
Generated from: `transcription_fixes_changelog.md`
