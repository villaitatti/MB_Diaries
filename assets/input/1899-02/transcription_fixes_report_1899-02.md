# Transcription fixes — 1899-02

Source: `assets/input/1899-02/1899-02.docx`

**5** fixes applied · **2** reviewed, no fix needed

## Fixes applied

### `1899-02-01` — double period glued to next sentence's capital letter

```diff
- Poggio..Bernhard met
+ Poggio. Bernhard met
```

### `1899-02-02` — missing space after quote mark opening quoted letter excerpt

```diff
- …”I wrote thus far
+ …” I wrote thus far
```

### `1899-02-03` — page marker glued inside the word white-haired on both sides

```diff
- white-[0029]haired
+ white- [0029] haired
```

### `1899-02-04` — page marker glued to adjacent editorial bracket note

```diff
- [0232][three lines
+ [0232] [three lines
```

### `1899-02-05` — word-glue compound: ardour + the

```diff
- ardourthe question
+ ardour the question
```

## Reviewed, no fix needed

- **p.46** "the [Kerr-]Lawsons" — same bracketed-insertion convention as 1898-99 p.27 ("Mrs. [Kerr-]Lawson"); the bracket is intentionally glued to the base word to disambiguate the hyphenated surname, not a missing space. Left as-is.
- **p.381** "overtook", **p.514**/**p.538** "Engerand" (a real surname, appears twice), **p.1019** "Hartland" (a real surname) — Category B word-glue false positives: each is a single real word/proper noun ending in one of the scanner's glue suffixes ("took"/"and"/"land"). No fix needed.

---
Generated from: `transcription_fixes_changelog.md`
