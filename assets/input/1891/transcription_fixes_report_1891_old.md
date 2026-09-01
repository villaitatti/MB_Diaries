# Transcription fixes — 1891_old

Source: `assets/input/1891/1891_old.docx`

**2** fixes applied · **1** reviewed, no fix needed

## Fixes applied

### `1891_old-01` — missing space after page marker [0105]

```diff
- [0105]lyrical
+ [0105] lyrical
```

### `1891_old-02` — missing space after closing quote before capital letter

```diff
- – – –!”Who doesn’t at any rate
+ – – –!” Who doesn’t at any rate
```

## Reviewed, no fix needed

- **p.1591** `Monday, June <20> [019], 1892, Paris` — flagged in Category C because `[019]` is immediately followed by a comma. All six flagged Category C candidates in this file (p.1591, 1667, 1670, 1673, 1675, 3245) share this exact shape: a *3-digit* bracketed number embedded mid-sentence in a date-header line, directly followed by a comma before the year (e.g. `August 16 [015], 1892`). This diary's genuine page markers are a different, 4-digit convention (`[0076]`) that sits alone at the start of its own paragraph/page — these 3-digit brackets are a second, unrelated annotation convention (paired with the diarist/editor's angle-bracket date corrections like `<20>`, `〈16〉` seen in the same lines), and a bracket directly followed by a comma is completely normal English punctuation, not a missing-space glue bug. Left as-is on all six.

---
Generated from: `transcription_fixes_changelog_1891_old.md`
