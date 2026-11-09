# Transcription fix log — 1896-98.docx

Generated: 2026-10-01T08:50:17.826693+00:00
Fixes definition: `/private/tmp/claude-502/-Users-gspinaci-projects-mb-diaries-MB-Diaries/bb845fdf-3d23-4581-acfb-c8509cb1a933/scratchpad/1896-98_fixes_reviewer1.json`

## Applied (14)

- **page11-remove-underline-add-quotes** p.11 — Reviewer: "Central Italian Painters" should be quoted (as in the manuscript), not underlined. Manuscript image (IIIF canvas seq.11, ms p.3) shows the title in double quotes, no underline.
  - `his Central Italian Painters in` → `his “Central Italian Painters” in`
- **page22-date-swap-wed** p.22 — Reviewer: bracketed/plain dates are swapped. Manuscript (IIIF canvas seq.14, ms p.14) literally reads 'Wednesday Nov. 10' -- the literal written date belongs in the plain text, the editorial correction in brackets.
  - `Wednesday Nov. 11 [written: 10]. 1896. Fiesole` → `Wednesday Nov. 10 [written: 11]. 1896. Fiesole`
- **page23-date-swap-thu** p.23 — Reviewer: bracketed/plain dates are swapped. Manuscript (IIIF canvas seq.16, ms p.16) literally reads 'Thursday Nov. 11'.
  - `Thursday, Nov. 12 [written: 11]. 1896, Fiesole` → `Thursday, Nov. 11 [written: 12]. 1896, Fiesole`
- **page23-date-swap-fri** p.23 — Reviewer: bracketed/plain dates are swapped. Manuscript (IIIF canvas seq.16, ms p.16) literally reads 'Friday Nov. 12'.
  - `Friday, Nov. 13 [written: 12]. 1896` → `Friday, Nov. 12 [written: 13]. 1896`
- **marker-24** p.24 — Malformed dual-number marker ('transcription-count/ms-page') not matched by the page regex, collapsing pages 24-30 into page 23. Corrected to the sequential transcription page number (confirmed against IIIF canvases seq.24-32).
  - `[0024/0026]` → `[0024]`
- **marker-25** p.25 — Same malformed-marker issue as marker-24.
  - `[0025/0027]` → `[0025]`
- **marker-26** p.26 — Same malformed-marker issue; second number (18) is the manuscript's own page number (ms p.18), confirmed via IIIF canvas seq.26.
  - `[0026 18]` → `[0026]`
- **marker-27** p.27 — Transcriber's running count had drifted to 29/30 here; corrected to the true sequential number 27 (ms p.19, confirmed via IIIF canvas seq.27).
  - `[0029 19]` → `[0027]`
- **marker-28** p.28 — Same drift as marker-27; corrected to 28 (ms p.20, confirmed via IIIF canvas seq.28).
  - `[0030 20]` → `[0028]`
- **marker-29** p.29 — Pre-existing clean marker was mislabeled '31' due to the same drift; this content is ms p.21 (confirmed via IIIF canvas seq.29) and must be page 29 to keep page_number aligned with the IIIF canvas index used by rdf.py.
  - `[0031]` → `[0029]`
- **marker-30** p.30 — Same drift as marker-29; this content is ms p.22 (Fri Nov.20/Sat Nov.21, confirmed via IIIF canvas seq.30) and must be page 30.
  - `[0032]` → `[0030]`
- **marker-31** p.31 — Same drift; this content is ms p.23 (confirmed via IIIF canvas seq.31) and must be page 31 so the reviewer-reported seq.31/32 image mismatch resolves.
  - `[0034]` → `[0031]`
- **marker-32** p.32 — Same drift; this content is ms p.24 (Mon Nov.23/Tue Nov.24, confirmed via IIIF canvas seq.32) and must be page 32.
  - `[0035]` → `[0032]`
- **page16-underline-harmony-modelling** p.16 — Reviewer: 'is like modelling' should be underlined. Manuscript image (IIIF canvas seq.16, ms p.8) shows 'harmony is like modelling' underlined; the run currently carries no formatting at all.
  - `harmony is like modelling` → `<underline>harmony is like modelling</underline>`

## Correction (2026-10-01): marker-31/marker-32 were off by one

After regenerating output, pages 31-33 did not match expectations: a pre-existing,
untouched `[0033]` marker (docx paragraph 129, between the old `[0032]` and `[0034]`)
had been missed when drafting `marker-31`/`marker-32` above, so renaming `[0034]->[0031]`
and `[0035]->[0032]` left the numbering one marker short — page 31 ended up holding the
Nov.23/24 content (meant for page 32), and page 33 kept the Bernhard/Duccio/Caves content
(meant for page 31).

Fixed by a direct, index-targeted 3-way rotation (not a text find/replace, since the
intermediate state would have produced duplicate marker text):
- docx paragraph 129: `[0033]` → `[0031]` (content: "taught her to think...Duccio...Caves", ms p.23, canvas seq.31)
- docx paragraph 132: `[0031]` → `[0032]` (content: "Monday Nov.23...Tuesday Nov.24...problem play", ms p.24, canvas seq.32)
- docx paragraph 138: `[0032]` → `[0033]` (content: "much more than as a work of art...", restores this span to page 33, previously mislabeled 32)

Re-verified against `pages.json`: page 31 now holds the Duccio/Caves content, page 32 the
Nov.23/24 content — matching their respective IIIF canvases (seq.31, seq.32) and resolving
the reviewer's seq.31/32 image-mismatch report.

## Round 2 (2026-10-01): pages 34-60 drift (`[0036 26]`, "Friday 27" region)

User report: "diary 4 has other issues. From sequence 33, there is friday 27 which
should be in the next sequence. For instance, 'and he suddenly thought [0036 26] God
couldn't be omnipotent' should be checked." This is the same transcription-count-drift
pattern as the pages 24-32 fix above, recurring starting right after page 33.

Confirmed against IIIF canvases seq.34, seq.35, seq.57, seq.58, seq.59 (ms pages
"26"/"27"/"49"/"50"/"51" — note handwritten ms page numbers do **not** follow a simple
offset from the canvas index in this manuscript, so every boundary was verified by
content-matching the docx text against the actual manuscript image, not by arithmetic
on the handwritten numbers): the transcriber's running page count had drifted by 2
starting at paragraph 143 (content that should start a new page, "God couldn't be
omnipotent...", was instead left attached to the end of page 33), and stayed off by
exactly 2 through the clean markers `[0037]`...`[0059]`, confirming canvas seq.57's
content ends exactly at the second malformed marker `[0061 51]`, and canvas seq.59's
content ("Monday Jan.25.97...") begins there.

Applied as a single atomic token-substitution pass (each old marker string mapped
directly to its new value and substituted in one `re.sub` scan per paragraph, to avoid
the sequential-replace cascade bug from the Round 1 correction above):

- `[0036 26]` (para 143) → `[0034]`
- `[0037]` → `[0035]`, `[0038]` → `[0036]`, `[039]` → `[0037]`, `[0040]` → `[0038]`,
  `[0041]` → `[0039]`, `[0042]` → `[0040]`, `[0043]` → `[0041]`, `[0044]` → `[0042]`,
  `[0045]` → `[0043]`, `[0046]` → `[0044]`, `[0047]` → `[0045]`, `[0048]` → `[0046]`,
  `[0049]` → `[0047]`, `[0050]` → `[0048]`, `[0051]` → `[0049]`, `[0052]` → `[0050]`,
  `[0053]` → `[0051]`, `[0054]` → `[0052]`, `[0055]` → `[0053]`, `[0056]` → `[0054]`,
  `[0057]` → `[0055]`, `[0058]` → `[0056]`, `[0059]` → `[0057]`
- `[0061 51]` (para 267, second malformed marker) → `[0059]`
- `[0062]` (para 271) → `[0060]`

Re-verified against regenerated `pages.json`: page 34 now starts "God couldn't be
omnipotent...", page 35 "of him in the 'Quarterly'...", page 56 "endow a Theatre...",
page 57 ends "...married to him)" (matching canvas seq.57/58's content, including the
very faint "Theatre / Alice Taylor / paradoxical / The Master" passage bleeding through
on canvas seq.58), page 59 "Monday Jan.25.97. Fiesole...", page 60 "Wednesday
Jan.27.1897...". `verify_output_matches_source.py --diary 1896-98` passes (176 pages)
after removing 2 stale output HTML files left over from the pre-fix page numbering
(`1896-98_58.html`, `1896-98_62.html`, gitignored, not repo-tracked).

Note: pages 58, 61 and 62 are now gaps (no page with that number) — this is expected,
not a regression: page 58 has no content of its own (its content was captured inline
within page 57's span, per canvas seq.58 above), and 61/62 are a boundary artifact of
stopping this fix at page 60 (see follow-up below) rather than new data loss.

## Round 3 (2026-10-01): underline all day/date headers

Reviewer images (e.g. IIIF canvas seq.59, ms p.51: "Monday. Jan. 25.97. Fiesole")
confirmed the manuscript consistently underlines the whole dateline — day name,
date, and any place name on the same line — but none of the 247 date-header
paragraphs in the docx carried underline formatting; this was a systematic,
diary-wide transcription gap, not a handful of isolated cases (verified by
sampling the longest and shortest matches, no false positives among paragraphs
starting with a weekday name).

Applied `run.underline = True` to all 247 day-header paragraphs (matched by a
`^(weekday)[,.]?\s+[A-Z]` anchor). 4 of them contain an editorial bracket note
we added ourselves (`[written: 11]`, `[written: 12]`, `[written: 13]` from the
Round-1 date-swap fix, plus a pre-existing `[i.e. 20]`) — these are not part of
the manuscript's literal handwriting, so each such run was split into
before/bracket/after, underlining only the before/after text and leaving the
bracket itself plain (reusing `fix_transcription_issues._split_run_around`).
2 headers (para 814, 835) had harmless extra empty/whitespace runs from earlier
edits; only the non-whitespace run was underlined.

`verify_output_matches_source.py --diary 1896-98` passes (176 pages, unaffected
since underline is formatting-only); spot-checked rendered HTML for pages 15 and
22 to confirm `<u>...</u>` wraps the header text and correctly excludes the
bracket note. `--all` still 25/25 PASS.

## Round 4 (2026-10-01): underline fix missed 18 non-standard headers

User report: page 9 ("Oct. 30, 1896. Friday. Villa Rosa Fiesole") had no
underline after Round 3. Round 3's `^(weekday)[,.]?\s+[A-Z]` anchor only
matched headers that *start* with the weekday name, missing other dateline
formats actually present in this docx. A full re-scan (any paragraph under
100 chars containing a weekday name or a month abbreviation + digit, not yet
underlined) found 24 more candidates; 5 were transcriber's editorial notes
about manuscript gaps (e.g. "no entries after May 6 until May 27:", "top of
page with entries for April 31-May 2 torn away") — correctly not headers, left
alone — and 19 were genuine missed headers in three further formats:

- Date-first ("Oct. 30, 1896. Friday. Villa Rosa Fiesole", "April 14.97.
  Wednesday.") — underlined whole.
- Asterisk-prefixed ("* Friday Nov. 6. 1896. Fiesole.", 11 instances) — split
  so only the dateline after "* " is underlined, leaving the asterisk marker
  itself plain (same split-run approach as the bracket cases in Round 3).
- Marker-prefixed ("[0059] Monday Jan. 25.97. Fiesole", "[0142] Thursday
  Sept. 2. 1897...", "[0150 138] Saturday Oct. 30.97...") — split the same
  way, excluding the page-marker bracket from the underline.

One further candidate, para 558 `[Thursday April 29. 1897.]`, was deliberately
**left un-underlined**: unlike the other bracket cases, the entire dateline is
inside the brackets with nothing outside them, suggesting this date is an
editorial reconstruction (the entry's real written date is missing/illegible
in the manuscript, per the "entries for April 22-28 missing" / "top of page
... torn away" notes immediately surrounding it) rather than literal
transcribed handwriting — there is no real manuscript ink here to underline.
Flagged below for a human call if that reading is wrong.

Re-verified: `verify_output_matches_source.py --diary 1896-98` passes (176
pages); spot-checked pages 9, 10, 59, 143, 190 render `<u>...</u>` around the
full dateline. `--all` still 25/25 PASS.

## Round 5 (2026-10-01): marker drift fix, continued (pages 61-94)

User report: "The HTML files for sequences 61 and 62 are missing. 63 has the
content that 61 should have." This is exactly the follow-up flagged below
after Round 2 — the same -2 transcription-count drift, continuing past the
`[0062]`→`[0060]` stopping point into the next clean run of markers (docx
paragraphs 277-443).

Confirmed via `pages.json` before the fix: page 60 contained both the
"Wednesday Jan.27" and "Thursday Jan.28" entries merged together (no separate
marker for the latter exists in the docx — a pre-existing transcriber
omission, same category as the already-accepted page-58 gap from Round 2, not
something newly broken), and page 63 held the "Friday Jan.29" content that
should have been page 61.

Applied the same atomic single-pass token-substitution technique as Round 2
(one regex pass per paragraph, looked up against the original text, so
overlapping old/new values can't cascade):

```
[0063]->[0061]  [0064]->[0062]  [0065]->[0063]  [0066]->[0064]  [0067]->[0065]
[0068]->[0066]  [0069]->[0067]  [0070]->[0068]  [0071]->[0069]  [0072]->[0070]
[0073]->[0071]  [0074]->[0072]  [0075]->[0073]  [0076]->[0074]  [0077]->[0075]
[0078]->[0076]  [0079]->[0077]  [0080]->[0078]  [0081]->[0079]  [0082]->[0080]
[0083]->[0081]  [0084]->[0082]  [0085]->[0083]  [0086]->[0084]  [0087]->[0085]
[0088]->[0086]  [0089]->[0087]  [0090]->[0088]  [0091]->[0089]  [0092]->[0090]
[0093]->[0091]  [0096]->[0094]
```

The original docx already skipped straight from `[0093]` to `[0096]` (no
094/095 markers existed before this fix either) — a pre-existing 2-page gap,
preserved as new pages 92/93, not newly introduced by this fix.

Verified against regenerated `pages.json`: page 61 now starts "Friday Jan. 29.
1897." (matching the user's report), page 62 "Monday Feb. 1. 1897.", page 63
"Wednesday Feb. 3. 1897." Deleted 3 stale gitignored orphan HTML files
(`1896-98_92/93/96.html`) left over from the pre-fix numbering, in both
`assets/output/1896-98/html/` and the `apps/MB_Diaries-app/file/` mirror.
`verify_output_matches_source.py --diary 1896-98` passes (176 pages); `--all`
still 25/25 PASS.

Deliberately stopped again at the next malformed dual-number marker
`[0097 85]` (para 447) — same scoping precedent as Round 2's stop at
`[0061 51]` — since determining its correct value needs the same IIIF
content-matching verification, not just arithmetic continuation of the -2
offset.

## Round 6 (2026-10-01) — marker drift, `[0097 85]` through `[0191]` (pages 95-189)

User report: "sequence 94 contains \"[0097 85]\" but it should start sequence 95.
from there the sync is wrong again." This reopens exactly the malformed marker
flagged as the next resync point at the end of Round 5.

A **new** -2 drift begins exactly at the malformed marker `[0097 85]` (para 447) —
it is not a continuation of Round 5's offset, which had already reset to 0 by the
native `[0094]` marker at para 443 (confirmed via IIIF canvas seq.94, ms p."84.",
matching "having formed the habit...Hugh Morgan" exactly — left untouched).

A full-document regex scan confirmed `[0097 85]`, `[0130 118]`, `[0150 138]` (plus
an editorial-looking `[0115 'Letter to Reinach']`) are the **only** malformed
digit-bracket markers anywhere in the 933-paragraph document. Each was
content-matched against its IIIF canvas, and all four resolve to one uniform -2
offset holding continuously from para 447 all the way to the document's last
marker, `[0191]` (para 925):

- `[0097 85]` → `[0095]` — canvas seq.95, ms "85."
- `[0115 'Letter to Reinach']` → `[0113]` — canvas seq.113, ms "103.", with the
  literal "Letter to Reinach" marginal annotation visible on the scan
- `[0130 118]` → `[0128]` — canvas seq.128, ms "118"
- `[0150 138]` → `[0148]` — canvas seq.148, ms "138.", "Saturday Oct. 30.97. Villa
  Rosa Fiesole" matching exactly
- `[0191]` → `[0189]` — canvas seq.189, ms "179.", "Thursday Dec. 23.97" / "Friday
  Dec. 24.97" matching exactly — confirms the offset holds uniformly through the
  end of the document, no further undetected drift beyond this point

Applied as one atomic pass across paragraphs 447-925 (96 markers total: every
`[0098]`...`[0190]` shifted by -2, plus the 4 malformed markers above collapsed to
a single clean bracket each). `[0115 'Letter to Reinach']` was split across 4 runs
in the source and was reassembled into a single `[0113]` token.

A first attempt also shifted the native `[0094]` marker at para 443 by mistake —
it sits *before* this drift begins and was already correct. Caught via the same
canvas seq.94 image check and reverted before regenerating output.

Two pre-existing, out-of-scope irregularities surfaced by this same scan were left
untouched (no reviewer complaint, not part of this report) — see Follow-up below.

Regenerated and verified: `pages.json` now has 180 pages (4-189), with pages 92/93
missing (two blank manuscript leaves — canvas seq.92/93 show only faint
bleed-through, matching the pre-existing "94-95: two blank pages" editorial note at
para 442), page 58 missing (pre-existing, already-confirmed blank leaf), and page
172 missing (pre-existing gap, see Follow-up) — no other gaps. Deleted 4 stale
gitignored orphan files per page (92, 172, 190, 191) from
`assets/output/1896-98/{html,txt,ttl/document}` and the `apps/MB_Diaries-app/file/`
mirror, left over from the pre-fix numbering (old max page was 191, now 189).
`verify_output_matches_source.py --diary 1896-98` passes (180 pages); `--all`
still 25/25 PASS.

## Round 7 (2026-10-01) — duplicate-marker split, page 169/170 (pages 170-190)

User report: "sequence 169 should end at 'For instance, I asked her whether it
was', while [...] should be in page 170. The other are out of sync." This is
exactly the duplicate-marker irregularity flagged as a Round 6 follow-up: para
839 contains two separate marker occurrences that both carried the same raw
value (171 originally, `[0169]` after Round 6's -2 shift), so the pipeline's
duplicate-merge behavior concatenated both segments into a single page instead
of splitting them. The second occurrence is a genuine transcription undercount
(should have been 172, not a repeat of 171) — not a true duplicate — so this is
a one-off **+1** resync starting at that exact point, not a continuation of the
uniform -2 pattern from Rounds 2/5/6.

Fix: changed the second `[0169]` occurrence in para 839 (the one preceding "not,
as a matter of fact, possible to take in aesthetically...") to `[0170]`, and
shifted every subsequent marker by **+1** through the end of the document
(para 840's `[0171]`→`[0172]` ... para 925's `[0189]`→`[0190]`; 17 runs across
paragraphs 840-925, plus the 2 edits inside para 839).

Verified against regenerated `pages.json`:
- page 169 now ends "...whether it was"
- page 170 starts "not, as a matter of fact...the slightest" – and this a
  question..."
- page 171 starts "brain-exhaustion?" / "Then we had a lugubrious tea..."

— matching the user's report exactly. `pages.json` now has 181 pages (4-190);
the pre-existing unrelated gap (skipped marker, see below) shifted from page 172
to page 173 along with everything else, still present and still unexplained by
any editorial note. Deleted 1 stale gitignored orphan file per page (173) from
`assets/output/1896-98/{html,txt,ttl/document}` and the
`apps/MB_Diaries-app/file/` mirror. `verify_output_matches_source.py --diary
1896-98` passes (181 pages); `--all` still 25/25 PASS.

## Round 8 (2026-10-01) — page-173 gap was not legitimate after all, closed

The user initially confirmed the page-173 gap as correct, then retracted that
after checking the manuscript directly: "page 173 content is 'mourners, and a
more cordial farewell to Miss Paget, we came away...'" — i.e. the gap was never
a real blank/skip, it was the tail end of the same drift pattern fixed in
earlier rounds, just not caught by Round 7's spot checks.

Confirmed via IIIF canvas content-matching:
- canvas seq.172 (ms "162") matches current page 172 exactly — no drift there.
- canvas seq.173 (ms "163") matches the content then labeled page 174
  ("mourners...deepened").
- canvas seq.174 (ms "164") matches the content then labeled page 175
  ("Saturday Nov.27...Sunday Nov.28...").

So the marker that read `[0174]` in para 840 (right after the already-correct
`[0172]`) was wrong — it should never have skipped 173 — and everything after
it was off by +1 relative to its canvas.

Fix: changed para 840's `[0174]` to `[0173]` (closing the gap entirely), then
shifted every subsequent marker down by **1** through the end of the document:
para 842 `[0175]`→`[0174]`, para 849 `[0176]`→`[0175]`, para 855
`[0177]`/`[0178]`→`[0176]`/`[0177]`, para 855 `[0179]`→`[0178]`, para 858
`[0180]`→`[0179]`, para 869 `[0181]`→`[0180]`, para 878 `[0182]`→`[0181]`,
para 888 `[0183]`→`[0182]`, para 895 `[0184]`→`[0183]`, para 901
`[0185]`→`[0184]`, para 908 `[0186]`→`[0185]`, para 910 `[0187]`→`[0186]`,
para 912 `[0188]`→`[0187]`, para 916 `[0189]`→`[0188]`, para 925
`[0190]`→`[0189]`.

Net effect: the document's last page reverts from 190 back to 189, which
re-matches the Round 6 end-of-document verification (canvas seq.189 / ms
"179", "Thursday Dec.23.97...rotten eggs...") that held before Round 7's
duplicate-split +1 shift — confirming Round 7's shift had introduced one too
many pages overall, now absorbed by closing this gap instead of extending the
tail.

Verified against regenerated `pages.json`:
- 181 pages (4-189), gap closed
- page 173 starts "mourners, and a more cordial farewell..."
- page 174 starts "Saturday Nov. 27. 1897..."
- page 189 still ends "...rotten eggs..."

Deleted 1 stale gitignored orphan file (190) from
`assets/output/1896-98/{html,txt,ttl/document}` and the
`apps/MB_Diaries-app/file/` mirror. `verify_output_matches_source.py --diary
1896-98` passes (181 pages); `--all` still 25/25 PASS.

## Round 9 (2026-10-01) — attached Diary 4B (pages 190-237)

User request: attach a separate continuation-diary file, `Diary 4B.docx` (360
paragraphs, found already sitting in `assets/input/1896-98/`, content starting
"Il Frullino - San Domenico di Fiesole" / "Christmas Day 1897."), onto the end
of `1896-98.docx`, with correct page numbering continuing the sequence,
verified against the IIIF manuscript scans.

**Marker cleanup.** Diary 4B's own markers were malformed dual-number tokens
(`[NNNN MSPAGE]`, `[NNNNa/b MSPAGE]`, `[NNNN s.n.]` — 47 total, `[0193 181]`
through `[0237 s.n.]`), none matched by the page-marker regex. Confirmed via
IIIF canvas content-matching (canvas190/ms"180", canvas191/ms"181",
canvas224/ms"214", canvas235/ms"225") that

```
correct_sequential_page = ms_page_number + 10
```

holds uniformly across the whole range, with two special cases:
- `[0225a 214]`→`[0224]`, `[0225b 215]`→`[0225]` — two interpolated
  half-numbered manuscript leaves, confirmed via canvas inspection as genuine
  distinct physical pages, not a mis-split.
- `[0236 s.n.]`→`[0236]`, `[0237 s.n.]`→`[0237]` — confirmed via canvas236/237
  images as two genuinely separate unnumbered physical list pages ("Common
  Friends" list and an "R.I.P." list), not a false split.

All 47 markers were collapsed to clean sequential single-number brackets
`[0191]`-`[0237]`, each via an exact `(paragraph_index, run_index)` replace
guarded by an assert that the old token appears exactly once in that run (all
47 were single-run this time, unlike Round 6's multi-run `[0115 'Letter to
Reinach']` case).

**Merge.** Diary 4B's 360 paragraphs were appended onto `1896-98.docx` (933
paragraphs post-Round-8) via python-docx, copying each paragraph's text and,
per run, the bold/italic/underline/strike flags — matching exactly what
`convert.py`'s `_extract_paragraph`/`_extract_run`/`_get_run_type` read
(paragraph style/alignment is not consumed by the pipeline).

**Page-190 boundary bug.** Regenerating the pipeline after the merge showed
page 190 missing. `parse_pages()` walks paragraphs in reverse and assigns
content to the next marker encountered going backward; since Diary 4B's
lead-in prose has no marker before `[0191]`, and the old document's last
marker was `[0189]` with nothing in between at the seam, the old page-189 tail
and Diary 4B's un-marked lead-in both landed in page 189's bucket. Fixed by
inserting a new standalone paragraph `[0190]` immediately before Diary 4B's
first paragraph ("Il Frullino - San Domenico di Fiesole"), giving the
reverse-walk the boundary it needed.

**Verification.** Regenerated `pages.json`:
- 229 pages (4-237), same pre-existing gaps only ([5, 6, 58, 92, 93])
- page 189 ends "...The smell in the Frullino turns out to be – rotten
  eggs...still sleeping here."
- page 190 starts "Il Frullino - San Domenico di Fiesole" / "Christmas Day
  1897." / "Our final Moving...reading Exodus."
- page 191 starts "Sunday December 26. 1897..."
- page 224 = "Thursday March 3.98...tiring day."
- page 235 ends "...Wednesday Mar.31...charming voices."
- page 236 = the full "Common Friends" list (paragraphs 278-349, ending "Eva
  McLaren")
- page 237 = the "R.I.P." list (paragraphs 350-359, including the pencil
  annotation "1927 28 dead")

The now-redundant `Diary 4B.docx` (untracked, no git history, content fully
merged) was moved out of `assets/input` so it would no longer be
misidentified as a separate diary stem by `verify_output_matches_source.py
--all`'s glob-based stem discovery.

`verify_output_matches_source.py --diary 1896-98` passes (229 pages); `--all`
25/25 PASS. **No triplestore upload performed.**

## Follow-up (not fixed, out of scope)

One open item remains: the duplicate-marker pair noted in Round 6 (original raw
142 at paras 688/690, rendered as duplicate `[0140]`/now `[0141]`) was not
re-examined and may have the same kind of off-by-one issue as the page 169/170
(Round 7) and page 173 (Round 8) cases — both of which were initially
mis-assessed as fine until checked directly against the manuscript image.
Worth proactively re-verifying that region against its IIIF canvases rather
than waiting for another reviewer report, given the pattern of two prior
false-negatives in this same follow-up note.

## Skipped / needs manual review (0)

