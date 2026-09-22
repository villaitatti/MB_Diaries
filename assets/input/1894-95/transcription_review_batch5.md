# 1894-95 — what still needs checking against the scans

Companion to `transcription_fixes_changelog_batch5.md`. That file records the 9 corrections
applied to `1894-95.docx` in this round. **This file records what could *not* be fixed from the
text alone** — each item needs someone to look at the manuscript scans and decide.

Everything below was found while working through the reviewer's 14 reported items. None of it was
guessed at or silently patched.

---

## 1. Missing page markers (6 pages)

The diary is split into pages by `[NNN]` markers in the transcription. Six numbers have no marker
anywhere in the docx, so those pages are never created and never published: **71, 72, 80, 81, 156,
157**. The text is not lost — it is absorbed into the preceding page — but the page boundaries are
wrong, and the published site simply has no page 71, 72, 80, 81, 156 or 157.

These were **not** invented, because placing a marker means deciding where a manuscript page ends,
which requires the scans.

### 1a. Pages 71 and 72 — between `[070]` and `[073]`

The transcriber left an explicit note here:

> `[a page between p. 71 and p. 72 cut away.]`

The whole stretch between `[070]` and `[073]` is short — one date header and two short entries:

```
… more [070] wonderful, more beautiful than anything there. How covetous we felt!
Then we had a drive in the Bois. Alas! for our parting tomorrow.

Friday - August [31]. 1894
I left Paris at 8.20 - and Bernhard was to leave for Havre at one o'clock. We tried
not to be sentimental, but it is a great wrench, that horrible ocean!

Saturday  Sept. 1. 1894. Weisser Hirsch bei Dresden
A nice Harvard boy in "my" train - came over to study "the literature of the Romance
nations" in a year. He was a mixture of Fafner and Norman. We

[a page between p. 71 and p. 72 cut away.]

[073] Yes, it is clear if I wish to be a thinking being I must metaphysicize.
```

**To decide:** whether pp. 71 and 72 exist as scans at all (one page between them was physically
cut away, per the note), and if so where `[071]` and `[072]` belong. The dangling "We" before the
cut-away note suggests the text breaks mid-sentence at a page edge.

> Note: `Friday - August [31]. 1894` is an *editorial insertion of the day number*, not a page
> marker. It used to be misread as one — see section 4.

### 1b. Pages 80 and 81 — between `[079]` and `[082]`

Three complete daily entries sit in this stretch with no marker between them:

```
[079] Went to look at drawings in M. Chennevière's room upstairs - the Bellini
sketch-book, and the Codex Vallardi.

Friday Dec. 14. 1894
Bernhard called on Mrs. Perry and saw some Pissaro water-colour sketches …

Saturday Dec. 15. 1894
Drawings in portfolios in Louvre. Bernhard lunched with Bing …

Sunday. Dec. 16. 1894
Strange letter from HO. … and worked in the evening. [082]
```

**To decide:** where `[080]` and `[081]` fall among the Dec. 14 / 15 / 16 entries.

### 1c. Pages 156 and 157 — between `[155]` and `[158]`

Only **one** paragraph sits between these two markers:

```
… overwhelmed with Bernhard's genius. [155] simple, matter of fact, almost casual way -
as if Columbus had come back to Spain … He wants Bernhard to set to work on an
aesthetics at once.

In the afternoon we went to the Glaspalast to see Stoeving's picture, … We have not
dared to tell him yet that we fear he is not au fond a sculptor, and he has native bad
taste. German!! [158]
```

Two full manuscript pages (156, 157) would normally hold considerably more text than this.

**To check:** whether text is *missing* here as well as the markers — i.e. whether pp. 156-157 were
ever transcribed.

---

## 2. Date headers not underlined (8)

Date headers in this diary are underlined; 239 of them are. Two genuinely missing underlines were
fixed this round (p. 56 `Saturday, June 2, 1894, Florence` and p. 94 `Thursday, Jan. 31, 1895`).
Eight headers remain partly or wholly un-underlined. **Six are trivial and probably faithful to the
manuscript; two are worth a look.**

### Worth checking

| Page | Header | Issue |
|------|--------|-------|
| ~54 | `Thursday, May 3, 1894, Florence [crossed out]` | entirely plain. The `[crossed out]` note probably explains it — confirm that is what the scan shows. |
| ~151 | `Monday and Tuesday. July 8.9.95. Gasthaus zur Rose. Sterzing` | **inverted**: the date is plain and only the place name `Gasthaus zur Rose. Sterzing` is underlined. Every other header underlines the date. |

### Probably fine — trailing punctuation left outside the underline

These render as e.g. <u>Thursday. Feb. 22. 1894</u>. — a final full stop outside the underline.
Cosmetic, and plausibly exactly how the manuscript looks.

| Page | Header | Plain part |
|------|--------|------------|
| ~12 | `Thursday. Feb. 22. 1894.` | `.` |
| ~111 | `Sunday Mar. 10. '95. (Karin 6 years old!)` | `(Karin 6 years old!)` — a parenthetical aside, likely deliberate |
| ~116 | `Sunday. Mar. 24. 95. Fiesole.` | `.` |
| ~119 | `Monday April 1. 95.` | `.` |
| ~177 | `Thursday Oct. 3. 1895. Avignon. Hotel Crillon.` | `.` |
| ~200 | `Thursday Oct. 24. 1895. Villa Rosa. Fiesole.` | `.` |

---

## 3. Stale data on the published site — action needed before/with the next upload

**Pages 71 and 72 must be deleted from the triplestore by hand.**

An earlier run (December 2024) *did* publish a page 71, built with the old, wrong page boundaries.
Its content is the text that now correctly belongs to page 73 — which is precisely the
"Sequenza 71-73 — ripetizione" the reviewer reported: the site was serving the same text twice, once
as a 2024 page 71 and once as the current page 73.

The stale local copy (`apps/MB_Diaries-app/file/1894-95_71.html`, dated 20 Dec 2024) has been
deleted. **The triplestore copy has not been**, and will not be cleaned up automatically:
`upload.py` deletes only the graphs it is about to re-post. Since the pipeline no longer produces
pages 71 and 72, nothing will ever overwrite or remove them.

- **Pages 71, 72** — stale graphs from an earlier run. Must be **deleted manually** from the
  triplestore, or they will keep serving duplicated 2024 text.
- **Pages 142, 218** — were also missing before this round, but are now generated correctly, so the
  next upload overwrites them. No action needed.

---

## 4. For the record — why page 70 was losing 2/3 of its text

The reviewer's "Sequenza 70 — mancano 2/3 di pagina" was not a transcription error. The page-marker
pattern used for this diary also matched `[31]` in the editorial insertion
`Friday - August [31]. 1894`, so the pipeline treated it as "page 31" and moved the rest of page 70
there. Page 31 then carried text from two different parts of the diary.

Fixed by tightening the pattern for this diary to `\[0*\d{3}\]` (three digits required), which
matches all 214 real markers and excludes `[31]`. The insertion stays in the text, as it should.
