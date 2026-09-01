"""
General-purpose scanner for the kind of transcription glitches found (and
hand-fixed) in the 1891-93 diary: words or sentences glued together with no
whitespace, in ways the pipeline's own automatic whitespace fixer
(`_fix_missing_whitespace` in script.py, regex in
assets.scripts.const.regex_missing_whitespace) does not catch.

This is a READ-ONLY reporting tool. It never edits a .docx. For each
docx it is pointed at, it writes a Markdown report of candidate issues,
which a human then curates into a fixes JSON for
assets/scripts/fix_transcription_issues.py (see 1891-93_fixes*.json for
worked examples).

Why the pipeline's own fixer isn't enough (background):
  script.py inserts a space after `.!?;,:` when it's glued directly to the
  next word, UNLESS the following text looks like an abbreviation
  (`[A-Z]\\.`, e.g. "U.S."). That exception also silently protects glued
  names like "B." (Bernhard) -- "evening.B. had a cold" is exactly the kind
  of bug this never fixes. It also only fires when a word character follows
  the punctuation, so anything glued after a closing quote/paren/bracket
  ("Prince.”It was...") is entirely invisible to it. And it can't do
  anything about two whole words glued with NO punctuation between them at
  all ("Cavazzolaswhile").

This scanner reports three kinds of candidates:

  A. glued-punctuation, NOT auto-fixed by the pipeline
     (`.!?;:,)]"”` immediately followed by a capital letter). High
     confidence -- almost always a real bug once the false positives below
     are excluded.
  B. word-glue compounds (two words run together with no punctuation at
     all), detected via a curated list of common short glue-words. Lower
     confidence: real English/French/Italian/German words that happen to
     end the same way (husband, understand, England, meanwhile, ...) are
     excluded via WORD_GLUE_FALSE_POSITIVES, but that list is necessarily
     diary-specific and should be extended as new false positives turn up.
  C. an inline page-marker (e.g. "[146]") glued directly to the
     surrounding text with no space -- worth flagging on its own because
     _clean_vectors() splitting markers into their own paragraph can behave
     oddly when a marker has no surrounding whitespace, and it's the same
     root cause implicated in "page ends up merged with the next one"-style
     pagination complaints.

Usage:
    # Scan every diary under assets/input/*/*.docx
    python assets/scripts/scan_transcription_issues.py --all

    # Scan one diary
    python assets/scripts/scan_transcription_issues.py \
        --docx assets/input/1894-95/1894-95.docx

Reports are written to assets/output/<diary>/transcription_scan_report.md
(the output dir is created if missing).
"""

import argparse
import glob
import os
import re

from docx import Document

from assets.scripts import const

AUTO_FIXED_PATTERN = re.compile(const.regex_missing_whitespace)

# Category A: a "closer" character directly followed by a capital letter.
# Deliberately excludes the plain straight double-quote ("): unlike the
# curly “/” pair, a bare " is ambiguous (opens or closes a quotation) so
# `"George` right after a space is completely normal prose, not a glued-text
# bug, in diaries transcribed with straight quotes.
GLUED_CLOSER_PATTERN = re.compile(r'([\.!?;:,\)\]”])([A-Z])')

# Category C: an inline page marker with no whitespace on one or both sides.
MARKER_PATTERN = re.compile(const.regex_page_pattern)

# Category B: common short words that show up glued onto the end of the
# preceding word with no space. Kept deliberately small and unambiguous;
# expand as new diaries reveal new patterns.
WORD_GLUE_SUFFIXES = [
    "and", "the", "while", "wrote", "decided", "began", "went", "has",
    "have", "had", "was", "were", "took", "read", "found", "said", "asked",
    "made", "told", "gave", "came", "left", "saw", "called",
]

# Whole compounds that legitimately end in one of the suffixes above and
# must not be flagged. Extend this list rather than removing suffixes above
# when a new diary turns up more of these. Also see WORD_TOKEN_CROSSCHECK
# below, which catches most of this class generically -- this list is the
# fallback for words that only ever appear once in a given document (so the
# cross-check can't help) or that showed up often enough across diaries to
# be worth hard-coding.
WORD_GLUE_FALSE_POSITIVES = {
    "husband", "husbands", "understand", "understands", "understood",
    "england", "island", "islands", "inland", "demand", "demands",
    "switzerland", "zealand", "ireland", "scotland", "poland", "finland",
    "lapland", "mainland", "garland", "errand", "errands", "strand",
    "thousand", "thousands", "worthwhile", "meanwhile", "partook",
    "profound", "grand", "brand", "stand", "land", "sand", "hand", "hands",
    "gland", "bland", "expand", "expands", "wetland", "holland", "woodland",
    "command", "commands", "commanded", "recommend", "recommends",
    "breathe", "breathes", "goethe", "marthe", "ferdinand", "portland",
    "wonderland", "cleveland", "rutland", "maitland", "sutherland",
    "southerland", "hildebrand", "newfoundland", "rostand", "misunderstand",
    "overtook", "overcame", "engerand", "hartland", "bourland", "marquand",
    "washstand", "shorthand", "beforehand", "rowland", "fairyland",
    "underhand", "typewrote", "iolanthe", "younghusband", "carrand",
    "lenormand", "berchtold", "wermland", "cooksaw", "widespread",
    "disband", "talleyrand", "undertook",
}


def _full_text_with_paragraph_index(document):
  """Return list of (paragraph_index, paragraph_text) for body + table cells."""
  out = []
  for i, paragraph in enumerate(document.paragraphs):
    out.append((("p", i), paragraph.text))
  for ti, table in enumerate(document.tables):
    for ri, row in enumerate(table.rows):
      for ci, cell in enumerate(row.cells):
        for pi, paragraph in enumerate(cell.paragraphs):
          out.append((("t", ti, ri, ci, pi), paragraph.text))
  return out


def _auto_fixed_positions(text):
  positions = set()
  for m in AUTO_FIXED_PATTERN.finditer(text):
    pos = m.start()
    prev_c = text[pos - 1] if pos > 0 else ''
    next_c = text[pos + 1] if pos + 1 < len(text) else ''
    if prev_c.isdigit() and next_c.isdigit():
      continue
    positions.add(pos)
  return positions


def _scan_glued_closer(text, auto_positions):
  results = []
  for m in GLUED_CLOSER_PATTERN.finditer(text):
    pos = m.start()
    cap_pos = m.end() - 1
    after_cap = text[cap_pos + 1] if cap_pos + 1 < len(text) else ''
    if after_cap == '.':
      # Looks like an abbreviation continuation (B.F.C.C., S.W., U.S. ...);
      # too risky to flag generically.
      continue
    if pos in auto_positions:
      continue
    results.append(pos)
  return results


def _document_vocabulary(paragraphs):
  """Every standalone (whitespace/punctuation-delimited) word used anywhere
  in the document, lowercased. Used to cross-check word-glue candidates: if
  the full "glued" compound already occurs as an ordinary, correctly-spaced
  word elsewhere in the same document (a surname mentioned more than once,
  a place name, an ordinary English word), it is almost certainly not a
  glue bug -- a real transcription glitch producing the exact same
  compound twice, by coincidence, in one diary is vanishingly unlikely.
  This does not catch a word that ONLY ever appears in its glued form
  (nothing to cross-check against), which is what WORD_GLUE_FALSE_POSITIVES
  is for."""
  vocab = set()
  for _para_id, text in paragraphs:
    for word in re.findall(r"[A-Za-z']+", text):
      vocab.add(word.lower())
  return vocab


def _scan_word_glue(text, vocabulary=frozenset()):
  results = []
  for suffix in WORD_GLUE_SUFFIXES:
    for m in re.finditer(r'([A-Za-z]{4,})(' + re.escape(suffix) + r')\b', text):
      whole = m.group(0).lower()
      if whole in WORD_GLUE_FALSE_POSITIVES or whole in vocabulary:
        continue
      # Require a real word boundary *before* the prefix, so we don't trip
      # on a glue-word that's just the tail end of a longer, unrelated word.
      start = m.start()
      before = text[start - 1] if start > 0 else ' '
      if before.isalpha():
        continue
      results.append(m.start())
  return results


def _scan_glued_marker(text, min_digits=3):
  results = []
  for m in MARKER_PATTERN.finditer(text):
    digits = re.search(r'\d+', m.group(0))
    if not digits or len(digits.group(0)) < min_digits:
      # Short bracketed numbers are usually the diarist/editor's inline
      # date-correction annotations (e.g. "Sept. 9 [8]. 1891" meaning "the
      # date is really the 8th"), not page markers. Real page markers in
      # these diaries run 3+ digits; adjust --marker-min-digits per diary
      # if that convention differs.
      continue
    before = text[m.start() - 1] if m.start() > 0 else ' '
    after = text[m.end()] if m.end() < len(text) else ' '
    if not before.isspace() or not after.isspace():
      results.append(m.start())
  return results


def _context(text, pos, radius=45):
  return text[max(0, pos - radius):pos + radius].replace("\n", "\\n")


def scan_document(docx_path, marker_min_digits=3):
  document = Document(docx_path)
  paragraphs = _full_text_with_paragraph_index(document)
  vocabulary = _document_vocabulary(paragraphs)

  auto_fixed_count = 0
  glued_closer = []
  word_glue = []
  glued_marker = []

  for para_id, text in paragraphs:
    if not text:
      continue
    auto_positions = _auto_fixed_positions(text)
    auto_fixed_count += len(auto_positions)

    for pos in _scan_glued_closer(text, auto_positions):
      glued_closer.append((para_id, _context(text, pos)))
    for pos in _scan_word_glue(text, vocabulary):
      word_glue.append((para_id, _context(text, pos)))
    for pos in _scan_glued_marker(text, marker_min_digits):
      glued_marker.append((para_id, _context(text, pos)))

  return {
      "docx": docx_path,
      "paragraphs": len(paragraphs),
      "auto_fixed_by_pipeline": auto_fixed_count,
      "glued_closer": glued_closer,
      "word_glue": word_glue,
      "glued_marker": glued_marker,
  }


def write_report(result, report_path):
  os.makedirs(os.path.dirname(report_path), exist_ok=True)
  lines = [
      f"# Transcription scan report — {os.path.basename(result['docx'])}",
      "",
      f"Source: `{result['docx']}`",
      f"Paragraphs scanned: {result['paragraphs']}",
      f"Glued-punctuation instances the pipeline will auto-fix at runtime: "
      f"{result['auto_fixed_by_pipeline']} (informational only, not listed)",
      "",
      f"## A. Glued punctuation NOT auto-fixed by the pipeline "
      f"({len(result['glued_closer'])})",
      "",
      "High confidence. Each of these needs a manual find/replace fix (see "
      "assets/scripts/fix_transcription_issues.py).",
      "",
  ]
  for para_id, ctx in result["glued_closer"]:
    lines.append(f"- `{para_id}`: …{ctx}…")

  lines += [
      "",
      f"## B. Possible word-glue compounds ({len(result['word_glue'])})",
      "",
      "Lower confidence — real words that happen to end the same way are "
      "excluded via a small blocklist, but it isn't exhaustive for every "
      "language mixed into these diaries. Review each before fixing.",
      "",
  ]
  for para_id, ctx in result["word_glue"]:
    lines.append(f"- `{para_id}`: …{ctx}…")

  lines += [
      "",
      f"## C. Inline page markers glued to surrounding text "
      f"({len(result['glued_marker'])})",
      "",
      "A marker with no whitespace on one or both sides. Worth checking: "
      "this is the same root cause implicated in pages ending up merged "
      "with the next one.",
      "",
  ]
  for para_id, ctx in result["glued_marker"]:
    lines.append(f"- `{para_id}`: …{ctx}…")

  with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("--docx", help="Scan a single .docx file")
  group.add_argument("--all", action="store_true",
                      help="Scan every assets/input/*/*.docx")
  parser.add_argument("--input-glob", default="assets/input/*/*.docx",
                       help="Glob used with --all")
  parser.add_argument("--marker-min-digits", type=int, default=3,
                       help="Minimum digit count for a bracketed number to "
                            "be treated as a page marker rather than an "
                            "inline date-correction annotation like '[8]'")
  args = parser.parse_args()

  docx_paths = [args.docx] if args.docx else sorted(glob.glob(args.input_glob))

  summary = []
  for docx_path in docx_paths:
    diary = os.path.splitext(os.path.basename(docx_path))[0]
    output_dir = os.path.join("assets", "output", diary.split("_")[0])
    report_path = os.path.join(output_dir, "transcription_scan_report.md")
    try:
      result = scan_document(docx_path, args.marker_min_digits)
    except Exception as e:  # noqa: BLE001 - keep scanning the rest
      print(f"FAILED  {docx_path}: {e}")
      continue
    write_report(result, report_path)
    summary.append((docx_path, result, report_path))
    print(
        f"{diary:12s}  A={len(result['glued_closer']):4d}  "
        f"B={len(result['word_glue']):4d}  "
        f"C={len(result['glued_marker']):4d}  -> {report_path}"
    )

  total_a = sum(len(r["glued_closer"]) for _, r, _ in summary)
  total_b = sum(len(r["word_glue"]) for _, r, _ in summary)
  total_c = sum(len(r["glued_marker"]) for _, r, _ in summary)
  print(f"\nTOTAL across {len(summary)} docx: A={total_a} B={total_b} C={total_c}")


if __name__ == "__main__":
  main()
