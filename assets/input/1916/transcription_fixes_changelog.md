# Transcription fix log — 1916.docx

Generated: 2026-09-01T10:10:32.391295+00:00
Fixes definition: `assets/scripts/fixes/1916_fixes.json`

## Applied (3)

- **1916-01** p.1824 — missing space: Viola/and
  - `Mr. Eyre and Violaand her husband` → `Mr. Eyre and Viola and her husband`
- **1916-02** p.450 — missing space after inline page marker [061]
  - `avec un peu de [061]travail, être conservée` → `avec un peu de [061] travail, être conservée`
- **1916-03** p.451 — missing space after inline page marker [062]
  - `tu l’aimera sans [062]contrainte, et il n’y aura pas besoin de` → `tu l’aimera sans [062] contrainte, et il n’y aura pas besoin de`
- **1916-04** p.1631 — missing space between initials: S[cott]/C[ecil] (marginal presence note)
  - `S[cott]C[ecil]` → `S[cott] C[ecil]` (in `G[eoffrey] S[cott]C[ecil] P[insent]`)
- **1916-05** p.1646 — missing space between initials: S[cott]/C[ecil] (marginal presence note)
  - `S[cott]C[ecil]` → `S[cott] C[ecil]` (in `G[eoffrey] S[cott]C[ecil] P[insent]`)
- **1916-06** p.1655 — missing space between initials: S[cott]/C[ecil] (marginal presence note)
  - `S[cott]C[ecil]` → `S[cott] C[ecil]` (in `G[eoffrey] S[cott]C[ecil] P[insent]`)
- **1916-07** p.1663 — missing space between initials: S[cott]/C[ecil] (marginal presence note)
  - `S[cott]C[ecil]` → `S[cott] C[ecil]` (in `G[eoffrey] S[cott]C[ecil] P[insent]`)
- **1916-08** p.1669 — missing space between initials: S[cott]/C[ecil] (marginal presence note)
  - `S[cott]C[ecil]` → `S[cott] C[ecil]` (in `G[eoffrey] S[cott]C[ecil] P[insent]`)

*Fixes 1916-04 through 1916-08 were applied by a one-off script targeting the
5 paragraph indices directly (python-docx, reusing
`fix_transcription_issues._apply_replacement_in_paragraph` to preserve run
formatting), not via the JSON-driven `fix_transcription_issues.py` CLI. All
5 paragraphs are byte-identical marginal "who was present" notes
(`G[eoffrey] S[cott]C[ecil] P[insent]`, i.e. Geoffrey Scott and Cecil
Pinsent) with no distinguishing text within the paragraph itself, so the
generic tool's whole-document uniqueness requirement can never disambiguate
between them (it reports AMBIGUOUS, occurrences=5, for any find string equal
to or shorter than the full paragraph). Direct index targeting was the only
way to apply this obviously-correct, identical fix to all 5 without risking
a wrong match elsewhere in the document.

## Skipped / needs manual review (0)

## Reviewed, no fix needed

- **p.194** "A heavy cold overcame me" — scanner flags `over` + `came` as a
  possible word-glue compound, but "overcame" is a single, correctly spelled
  English word. Left as-is.
- **p.1060** "Duchess of Southerland" — scanner flags `Souther` + `and`
  (tail end happens to spell the "and" glue-suffix), but "Southerland" is a
  single word (the diarist's spelling of the surname/title). Left as-is.
- **p.1061** "Duchess of Rutland" — same false-positive pattern as p.1060
  (`Rutl` + `and`); "Rutland" is a single word/title. Left as-is.
- **p.1084** "before they overtook me" — scanner flags `over` + `took`, but
  "overtook" is a single, correctly spelled English word. Left as-is.

