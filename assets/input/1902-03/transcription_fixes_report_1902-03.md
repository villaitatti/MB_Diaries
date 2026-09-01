# Transcription fixes — 1902-03

Source: `assets/input/1902-03/1902-03.docx`

**3** fixes applied · **3** reviewed, no fix needed

## Fixes applied

### `1902-03-01` — stray comma glued to place name after date, missing space

```diff
- 1902.,Siena
+ 1902. Siena
```

### `1902-03-02` — stray extra period glued to weekday header

```diff
- 1902. .Sunday
+ 1902. Sunday
```

### `1902-03-03` — missing space before page marker [p030]

```diff
- refreshment.[p030]
+ refreshment. [p030]
```

## Reviewed, no fix needed

- **p.572** "overcame", **p.853** "misunderstand" — Category B word-glue false positives: each is a single real English word ending in one of the scanner's glue suffixes ("came"/"and"). No fix needed.
- **p.566** "1902 [1903]." and **p.570** "1902 [1903]." — these `[1903]` brackets are the diarist/editor's inline year-correction annotation (the entry is dated "1902" but the year has turned over to 1903), the same kind of short bracketed annotation the scanner's own digit-count filter is meant to exclude; it only slipped through here because the annotation happens to have 4 digits. The bracket is followed immediately by a sentence-ending period, which is normal punctuation, not a missing space. Left as-is.
- **p.965** "people. [p205]. " — the page marker is followed immediately by a period, which is normal sentence-ending punctuation attached to a closing bracket, not a missing space. Left as-is.

---
Generated from: `transcription_fixes_changelog.md`
