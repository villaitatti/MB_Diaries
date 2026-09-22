# 1936 — blocking transcription issue

## The diary currently produces no RDF at all

1936 is the only diary in the corpus that fails the pipeline outright. It generates its
per-page text and HTML, but crashes before any Turtle is written, so **no 1936 page has
ever reached the triplestore**. `assets/output/1936/ttl/` is empty.

```
File "assets/scripts/rdf.py", line 316, in pages2graphs
    canvases[max(key - 1, 0)]['images'][0]['resource']['@id']
IndexError: list index out of range
```

## Cause: a transposed page marker, `[906]`

Paragraph 493 of `1936.docx` carries a standalone marker `[906]`. The diary has 404
scanned canvases in `1936.json`, so the pipeline creates a page 906 and then looks for a
906th image that does not exist.

The intended number is not in doubt — it sits between its two neighbours, with
consecutive dated entries on either side:

| paragraph | text |
|-----------|------|
| 491 | `[095]` |
| 492 | `Tuesday, 17 March, 1936` |
| **493** | **`[906]`**  ← should be `[096]` |
| 494 | `Wednesday, 18 March, 1936` |
| 495 | `[097]` |

`906` is a digit transposition of `096`.

## What we need

Confirmation from the scans that paragraph 493 is page 96, after which the marker can be
corrected to `[096]` in the source docx and 1936 regenerated and uploaded. We have not
made the edit ourselves: correcting page markers is a transcription decision, and the
standing instruction on this project is to report marker problems rather than infer them.

This is the single change that unblocks the whole diary.
