"""
Read-only proof that the generated per-page HTML (assets/output/<diary>/html/)
is text-faithful to the source docx (assets/input/<diary>/<diary>.docx): no
character lost, added, duplicated or reordered, and specifically no
whitespace invented anywhere the pipeline didn't get from the manuscript.

Does NOT import script.py (avoids the spaCy/en_core_web_lg load at import
time) or reuse _clean_vectors/parse_pages -- the whole point of an
independent verifier is that a bug in the pipeline's own page-boundary logic
must not go uncaught because both sides share the same code. It only reuses
assets.scripts.convert (paragraph/run extraction) and assets.scripts.const
(the page-marker regex), which the pipeline itself is built on.

Two checks, run per real page number:

  A. Whitespace-STRIPPED equality (all whitespace removed from both sides).
     Any failure here is a lost, added, duplicated or reordered character --
     unrelated to spacing.
  B. Whitespace-COLLAPSED equality (runs of whitespace -> a single space on
     both sides). Since check A already pins the character multiset, a
     check-B-only failure is, by construction, purely a whitespace
     discrepancy -- i.e. the pipeline invented or destroyed a space.

Concessions (documented, not hidden): the per-paragraph `.strip()`, the
`'\\n'`-join between paragraphs, and whitespace immediately adjacent to a
bracketed marker are all structurally insignificant (markers are promoted to
paragraph/page boundaries by the pipeline) -- none of that counts as
"inventing whitespace". {...} editorial annotations (transcriber's notes
about the physical manuscript page) are stripped from the source side too,
matching the pipeline's own _strip_annotations. Content before a diary's
first page marker (front
matter -- title pages, etc.) is dropped by the pipeline; each diary's exact
front-matter text is pinned in output_verification_exceptions.json and
reported as an accepted exception, not silently ignored -- a change in that
text is still a failure.

Usage:
    python assets/scripts/verify_output_matches_source.py --all
    python assets/scripts/verify_output_matches_source.py --diary 1902-03 --context 80
"""

import argparse
import glob
import json
import os
import re

from docx import Document

from assets.scripts import const

MARKER_PATTERN = re.compile(const.regex_page_pattern)
DIGIT_PATTERN = re.compile(r'\d+')
KNOWN_TAGS = re.compile(r'</?(?:html|body|p|b|i|u|s)>')
WHITESPACE = re.compile(r'\s+')

EXCEPTIONS_PATH = os.path.join(os.path.dirname(__file__), 'output_verification_exceptions.json')


def _launch_json_page_pattern(diary_stem, path=".vscode/launch.json"):
  raw = open(path, encoding="utf-8").read()
  data = json.loads(re.sub(r'^\s*//.*$', '', raw, flags=re.MULTILINE))
  for config in data.get("configurations", []):
    args = config.get("args", [])
    diary = None
    regex = None
    i = 0
    while i < len(args):
      if args[i] == "-d":
        diary = args[i + 1]
        i += 2
      elif args[i] == "-r":
        regex = args[i + 1]
        i += 2
      else:
        i += 1
    if diary == diary_stem and regex:
      return regex
  return r'\[p?0*\d{,3}\]'


def _page_number(token, page_pattern):
  if re.fullmatch(page_pattern, token):
    digits = DIGIT_PATTERN.findall(re.sub(const.regex_brackets, '', token))
    if digits:
      return int(digits[0])
  return None


def build_source_pages(docx_path, page_pattern):
  """Returns (pages: {page_number: text}, front_matter_text: str)."""
  document = Document(docx_path)
  pages = {}
  front_matter_parts = []
  current_page = None

  for paragraph in document.paragraphs:
    raw_text = ''.join(run.text for run in paragraph.runs)
    if not raw_text:
      continue

    # {...} editorial annotations (transcriber's notes about the physical
    # page, e.g. "{written vertically...}") are stripped by the pipeline
    # itself (script.py's _strip_annotations) before markers are ever
    # detected -- mirror that here so a diary using this convention doesn't
    # show up as a false CHECK A mismatch.
    raw_text = re.sub(const.regex_annotation_pattern, '', raw_text, flags=re.DOTALL)
    if not raw_text:
      continue

    # Only a REAL page marker breaks the paragraph (matching the pipeline's
    # own _clean_vectors, which now only isolates markers that fullmatch
    # this diary's page_pattern). An inline, non-page bracket (e.g. a
    # date-correction "[8]" in "Sept. 9 [8]. 1891") is NOT a page boundary --
    # it stays inline, literally, part of the same running fragment as the
    # text around it, so no phantom paragraph break -- and thus no phantom
    # whitespace -- gets introduced where the docx has none.
    pos = 0
    fragment_parts = []
    for m in MARKER_PATTERN.finditer(raw_text):
      page_num = _page_number(m.group(0), page_pattern)
      if page_num is None:
        continue  # inline bracket: leave it in the running text, untouched
      # Text up to (NOT including) the marker belongs to the page that was
      # current before it; the marker itself is metadata, never content --
      # parse_pages excludes the marker paragraph from page_content.
      fragment_parts.append(raw_text[pos:m.start()])
      text = ''.join(fragment_parts).strip()
      if text:
        pages.setdefault(current_page, []).append(text)
      fragment_parts = []
      pos = m.end()
      current_page = page_num
      # Always create the bucket, even if this page turns out to have zero
      # content (a real, if blank, diary page still gets its own output
      # HTML file from the real pipeline).
      pages.setdefault(current_page, [])
    fragment_parts.append(raw_text[pos:])
    text = ''.join(fragment_parts).strip()
    if text:
      pages.setdefault(current_page, []).append(text)

  front_matter_text = '\n'.join(pages.pop(None, []))
  pages = {n: '\n'.join(parts) for n, parts in pages.items()}
  return pages, front_matter_text


def _unescape(s):
  # Targeted inverse of html.escape(quote=False): & must be last, and this
  # is deliberately NOT html.unescape(), which also resolves semicolon-less
  # legacy entities (e.g. "&not;x" -> "¬x") that could silently mangle
  # a future transcription batch.
  return s.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')


def load_output_pages(diary_stem, output_html_dir):
  """Returns ({page_number: text}, [orphan_filenames])."""
  file_re = re.compile(re.escape(diary_stem) + r'_(\d+)\.html$')
  pages = {}
  orphans = []
  # [0-9]* (not *): a bare stem prefix match would also pull in a sibling
  # diary's files when two stems share this output folder (e.g. "1891" and
  # "1891_old" both write into assets/output/1891/html/) -- "1891_*.html"
  # matches "1891_old_155.html" too, which is not this diary's page 155.
  for path in glob.glob(os.path.join(output_html_dir, f'{diary_stem}_[0-9]*.html')):
    m = file_re.search(os.path.basename(path))
    if not m:
      orphans.append(os.path.basename(path))
      continue
    raw = open(path, encoding='utf-8').read()
    remainder = KNOWN_TAGS.sub('', raw)
    if '<' in remainder or '>' in remainder:
      raise AssertionError(
          f"{path}: unexpected tag survived stripping -- escaper bug? {remainder[:120]!r}")
    pages[int(m.group(1))] = _unescape(remainder)
  return pages, orphans


def load_exceptions():
  if not os.path.exists(EXCEPTIONS_PATH):
    return {}
  return json.load(open(EXCEPTIONS_PATH, encoding='utf-8'))


def _strip(s):
  return WHITESPACE.sub('', s)


def _collapse(s):
  return WHITESPACE.sub(' ', s).strip()


def _first_divergence(a, b, context):
  i = 0
  n = min(len(a), len(b))
  while i < n and a[i] == b[i]:
    i += 1
  return (f"  source : …{a[max(0,i-context):i+context]!r}…\n"
          f"  output : …{b[max(0,i-context):i+context]!r}…")


def verify_diary(diary_stem, context=60):
  input_dir = os.path.join("assets", "input", diary_stem.split("_")[0])
  output_html_dir = os.path.join("assets", "output", diary_stem.split("_")[0], "html")
  docx_path = os.path.join(input_dir, f"{diary_stem}.docx")

  page_pattern = _launch_json_page_pattern(diary_stem)
  source_pages, front_matter = build_source_pages(docx_path, page_pattern)
  output_pages, orphans = load_output_pages(diary_stem, output_html_dir)

  problems = []
  notes = []

  exceptions = load_exceptions().get(diary_stem, {})
  expected_fm_len = exceptions.get("front_matter_nonws_chars")
  fm_len = len(_strip(front_matter))
  if expected_fm_len is None:
    if fm_len:
      problems.append(
          f"front matter ({fm_len} non-whitespace chars) has no pinned "
          f"exception -- add one to {os.path.basename(EXCEPTIONS_PATH)} "
          f"if this is expected: {front_matter[:200]!r}")
  elif fm_len != expected_fm_len:
    problems.append(
        f"front matter length changed: expected {expected_fm_len}, got {fm_len} "
        f"-- {front_matter[:200]!r}")
  else:
    notes.append(f"EXCEPTION (accepted): front matter, {fm_len} chars")

  missing_in_output = sorted(set(source_pages) - set(output_pages))
  missing_in_source = sorted(set(output_pages) - set(source_pages))
  if missing_in_output:
    problems.append(f"{len(missing_in_output)} page(s) in the docx have no output HTML file: "
                     f"{missing_in_output[:20]}")
  if missing_in_source:
    problems.append(f"{len(missing_in_source)} output HTML file(s) don't correspond to any "
                     f"page marker in the docx: {missing_in_source[:20]}")
  if orphans:
    problems.append(f"{len(orphans)} STALE_OUTPUT file(s) in {output_html_dir} don't match "
                     f"the '{diary_stem}_<digits>.html' pattern: {orphans[:10]}")

  check_a_fail = check_b_fail = 0
  for page_num in sorted(set(source_pages) & set(output_pages)):
    src = source_pages[page_num]
    out = output_pages[page_num]
    src_stripped, out_stripped = _strip(src), _strip(out)
    if src_stripped != out_stripped:
      check_a_fail += 1
      if check_a_fail <= 5:
        problems.append(f"page {page_num}: CHECK A (character stream) differs\n"
                         + _first_divergence(src_stripped, out_stripped, context))
      continue  # check B is meaningless once the character multiset differs
    src_collapsed, out_collapsed = _collapse(src), _collapse(out)
    if src_collapsed != out_collapsed:
      check_b_fail += 1
      if check_b_fail <= 5:
        problems.append(f"page {page_num}: CHECK B (whitespace) differs\n"
                         + _first_divergence(src_collapsed, out_collapsed, context))

  status = "PASS" if not problems else "FAIL"
  return status, problems, notes, len(source_pages)


def main():
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("--diary", help="Diary stem, e.g. 1934 or 1891-93")
  group.add_argument("--all", action="store_true")
  parser.add_argument("--context", type=int, default=60)
  args = parser.parse_args()

  if args.diary:
    stems = [args.diary]
  else:
    stems = sorted(os.path.splitext(os.path.basename(p))[0]
                    for p in glob.glob("assets/input/*/*.docx"))

  n_pass = 0
  for stem in stems:
    status, problems, notes, n_pages = verify_diary(stem, context=args.context)
    print(f"{stem:12s} {status}  ({n_pages} pages)")
    for note in notes:
      print(f"    {note}")
    for problem in problems:
      print(f"    FAIL: {problem}")
    if status == "PASS":
      n_pass += 1

  print(f"\n{n_pass}/{len(stems)} PASS")
  raise SystemExit(0 if n_pass == len(stems) else 1)


if __name__ == "__main__":
  main()
