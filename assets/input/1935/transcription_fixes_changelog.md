# Transcription fix log — 1935.docx

Generated: 2026-09-01T10:10:37.854010+00:00
Fixes definition: `assets/scripts/fixes/1935_fixes.json`

## Applied (0)


## Skipped / needs manual review (0)

## Reviewed, no fix needed

All candidates in this diary's scan report (`assets/output/1935/transcription_scan_report.md`)
were Category B (possible word-glue compounds); Categories A and C were empty. Each was
checked against the full paragraph text in the docx and found to be a false positive:

- **p.401** "the Bernese Oberland" — real place name (a region of Switzerland), not a
  glued compound. Left as-is.
- **p.649** "Mr. Marquand of Princeton (1523)" — "Marquand" is a real surname (matches
  the word-glue suffix "-and"). Left as-is.
- **p.886** "Costa dead in Switzeland (1530)" — a misspelling of "Switzerland" (missing
  the "r"), but a single mangled word, not two words glued together with no space. Not
  a whitespace/glue bug, so out of scope for this tool; left as-is.
- **p.1209** "He was going to disband all the women's associations" — "disband" is a
  real English verb (matches the word-glue suffix "-and"). Left as-is.
- **p.2273** "Mr. and Mrs. Labendwere, Mr. and Mrs. Protheroe, Mary Straut" —
  "Labendwere" only occurs once in the document, so there is no other spelling to
  cross-check it against. It could plausibly be an unusual/foreign surname, or it could
  be a glued "Labend" + "were"/a mangled name — but nothing in the surrounding text
  (a plain list of "Mr. and Mrs. X" names) supports either reading confidently over the
  other, and there is no way to verify against the source. Left untouched rather than
  guess; flagging here for a human with access to the original transcript/source to
  confirm.

