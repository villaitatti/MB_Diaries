# Transcription fixes — 1898-99

Source: `assets/input/1898-99/1898-99.docx`

**2** fixes applied · **2** reviewed, no fix needed

## Fixes applied

### `1898-99-01` — double period glued to next sentence's capital letter

```diff
- Villa Viviani..Janet lunched
+ Villa Viviani. Janet lunched
```

### `1898-99-02` — missing space before page marker [0117]

```diff
- evening.[0117]
+ evening. [0117]
```

## Reviewed, no fix needed

- **p.27** "Mrs. [Kerr-]Lawson" — scanner flags `]L` as glued punctuation, but this is the diarist/editor's bracketed-insertion convention for disambiguating a hyphenated surname (the same pattern recurs as "the [Kerr-]Lawsons" in 1899-02 p.46); the bracket is deliberately glued to the base word by design, not a missing space. Left as-is.
- **p.132** "Hildebrand", **p.149** "Rostand", **p.286** "misunderstand" — Category B word-glue false positives: each is a single real word (a German surname and a common English verb) that happens to end in one of the scanner's glue suffixes ("and"/"stand"). No fix needed.

---
Generated from: `transcription_fixes_changelog.md`
