# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A digital-humanities ETL pipeline for the Mary Berenson Diaries (1891–1937). It takes a transcribed `.docx` per diary period, parses it into pages and paragraphs, enriches it (dates, locations, optionally NER/footnotes), serializes everything to CIDOC-CRM / Linked Open Data RDF (Turtle), and uploads the graphs to a ResearchSpace triplestore that powers https://mbdiaries.itatti.harvard.edu/. There is no test suite or build step — it is a one-shot CLI run per diary.

## Running the pipeline

The entry point is [script.py](script.py), a `click` CLI. The `PYTHONPATH` must include `assets/scripts` (set via [.env](.env); VS Code launch configs handle this automatically).

```bash
# Show options
python script.py --help

# Process one diary from a local docx (assets/input/<diary>/<diary>.docx)
python script.py -d 1907 -t 1907 -i 11

# Download the docx from Google Docs first, custom page regex, and concatenate
python script.py -d 1891-93 -t 1891-1893 -i 1 -gdoc <FILE_ID> -r '\[\d{3,}\]' --concatenate

# Process and upload RDF to the triplestore (uses [collection] section of psw.ini)
python script.py -d 1907 -t 1907 -i 11 -u -c collection
```

Key options: `-d` diary id (repeatable; required), `-u` execute upload, `-c` psw.ini section (default `localhost`), `-t` title, `-i` order index, `-gdoc` Google Doc file id, `-iiif` IIIF manifest URL, `-r` page-marker regex, `--concatenate` emit single-file text + stats.

[.vscode/launch.json](.vscode/launch.json) is the canonical run catalog — it has a ready-made full-pipeline config (diary id, title, index, Google Doc id, and the correct `-r` regex) for all 25 diary periods. **When running or debugging a specific diary, copy its args from there** rather than guessing — the per-diary page-marker regex in particular varies (see below).

There is no automated linting/testing. `autopep8`/`pycodestyle` are in requirements; the codebase uses 2-space indentation (not PEP8 4-space).

## Setup notes

- `pip install -r requirements.txt` — pulls spaCy and the `en_core_web_lg` model (NER is currently dormant in the main pipeline but the model loads at import time, so it is required).
- [assets/scripts/psw.ini](assets/scripts/psw.ini) holds triplestore credentials per section (`[localhost]`, `[collection]`, …) with `username`/`password`/`endpoint` keys. Required only for `-u`. See [assets/scripts/readme.md](assets/scripts/readme.md).

## Pipeline architecture

`exec()` in [script.py](script.py) drives a fixed sequence per diary. Data flows through a few well-defined shapes:

1. **docx → vectors** — [assets/scripts/convert.py](assets/scripts/convert.py) `convert2vec()` reads the docx via `python-docx` into `{document: [paragraph]}`, where each paragraph is `{text, runs:[{value, type, start_position, end_position}]}`. Run `type` captures bold/italic/underline/strike formatting.
2. **clean vectors** — `_clean_vectors()` splits page-marker tokens (e.g. `[0255]`) out of runs into their own paragraphs so markers become standalone delimiters. Detects markers against each paragraph's whole concatenated run text (not run-by-run), because Google Docs sometimes splits a marker across multiple runs at the character level.
3. **vectors → pages** — `parse_pages()` walks paragraphs *in reverse*, treating each paragraph whose full (stripped) text matches the page-marker regex as a page boundary, and groups the preceding paragraphs into that page. Produces an `OrderedDict[int, {text, content:[paragraph]}]`. Note `const.key_paragraphs == "content"`. If a page number repeats, its content is merged (never overwritten) and the repeat is logged to `assets/input/<diary>/duplicate_page_markers.md` — a repeated number is almost always a transcription mistake worth correcting at source.
4. **whitespace** — the pipeline no longer inserts whitespace at runtime: output text equals source docx text, character for character. Missing-whitespace-after-punctuation is instead migrated into the docx itself as a tracked, reviewable source change by [assets/scripts/migrate_missing_whitespace.py](assets/scripts/migrate_missing_whitespace.py) (see its module docstring for the AUTO/REVIEW/blocked classification), and [assets/scripts/verify_output_matches_source.py](assets/scripts/verify_output_matches_source.py) proves the property holds by comparing every generated page's text back against the docx.
5. **metadata** — `parse_metadata()` extracts diary-entry dates, preferring the generated HTML files, falling back to paragraph text. `is_valid_diary_date()` rejects dates outside the diary's year range (±5y) — this is how OCR garbage dates get filtered.
6. **RDF** — [assets/scripts/rdf.py](assets/scripts/rdf.py) builds CIDOC-CRM graphs: `diary2graphs` (the diary E22 object + IIIF image), `pages2graphs`/`create_page_graph` (one graph per page, with fulltext, IIIF image from the manifest canvas, and E12 Production / E52 Time-Span date nodes), and `create_annotation_graph` (W3C Web Annotation + CRMdig for footnotes). IIIF image URIs come from `<diary>.json` (a IIIF Presentation manifest in the input dir).
7. **upload** — [assets/scripts/upload.py](assets/scripts/upload.py) walks `output/<diary>/ttl/`, and for each `.ttl` does a DELETE-then-POST to the ResearchSpace `rdf-graph-store` endpoint (parallel, via `curl` + `os.system`). Graph URIs differ by subdir (`diary`/`annotation`/document).

The footnote/notes path (`parse_notes`, `parse_footnotes`, NER via `execute_ner`) is **currently commented out** in `exec()` — the live pipeline produces diary + page graphs only.

### Output layout (`assets/output/<diary>/`)

`pages.json`, `vectors.json` (intermediate JSON), `txt/<page>.txt` (per-page plain text — `rdf.py` reads these back for fulltext), `html/<diary>_<page>.html` (per-page styled HTML, `<`/`>`/`&` escaped, also mirrored into the external app dir, see below), `ttl/{diary,document,annotation}/*.ttl` (the RDF graphs), plus `error.log`. With `--concatenate`: `<diary>_concatenated.txt`, `<diary>_concatenated_with_conts.txt` (marks page continuations / mid-page date headers), and `<diary>_stats.json`.

## Per-diary quirks (important)

- **Page-marker regex varies per diary** and is passed via `-r`. The default is `\[p?0*\d{,3}\]`. Some diaries use `\[\d{3,}\]`, others `\[p\d+\]`, etc. The cleaning of raw transcripts into this `[NNNN]` marker convention is a **semi-automatic, manual regex process documented in [README.md](README.md)** ("Clean .txt diaries") — Google Docs export introduces ` ` and `<`/`>` artifacts that must be replaced before parsing.
- [assets/scripts/const.py](assets/scripts/const.py) centralizes every dict key, regex, header name, and the `diary_data`/`diaries` per-diary config maps. **Reference `const.*` constants rather than hardcoding string keys** — the JSON shapes use `value`/`runs`/`content`/`text` consistently through these.
- [script.py](script.py) line ~886 hardcodes an absolute `app_path` to a sibling `MB_Diaries-app` repo where HTML is mirrored. This is machine-specific and will silently no-op (caught exception) elsewhere.

## Narrative reference

[DIGITALIZATION_PROCESS.md](DIGITALIZATION_PROCESS.md) is a non-technical, public-facing description of the project for stakeholders — useful for domain context, not implementation detail.
