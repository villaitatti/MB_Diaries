# Transcription fixes — 1934

Source: `assets/input/1934/1934.docx`

**2** fixes applied · **3** reviewed, no fix needed

## Fixes applied

### `1934-01` — wrong-direction quotation mark used to open “Henry Esmond” (right double quote instead of left)

```diff
- more ”Henry Esmond”, but
+ more “Henry Esmond”, but
```

### `1934-02` — doubled opening bracket on page marker [172]

```diff
- [[172] Monday, June 4, 1934
+ [172] Monday, June 4, 1934
```

## Reviewed, no fix needed

- **p.538** "Went on with the Talleyrand as BB and I were alone." — the scanner flags `Talleyr` + `and` as a word-glue candidate, but "Talleyrand" is the proper noun (the book/subject Duff Cooper's biography, referenced again at p.662 and elsewhere), not two glued words. Left as-is.
- **p.662** "Nearly finished Duff Cooper's "Talleyrand in evng." — same false positive as p.538: "Talleyrand" is the book title, not a glue. Left as-is.
- **p.774** "Karin read me her lecture and I undertook to finish it." — the scanner flags `under` + `took` as a word-glue candidate, but "undertook" is an ordinary English word, not two words glued together. Left as-is.

---
Generated from: `transcription_fixes_changelog.md`
