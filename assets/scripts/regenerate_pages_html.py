"""
Regenerates the per-page output artifacts (assets/output/<diary>/{txt,html}/,
vectors.json, pages.json) straight from the current assets/input/<diary>/
<diary>.docx, WITHOUT touching Google Docs, RDF/TTL graphs, or the
ResearchSpace upload.

This exists to verify that the transcription fixes made to the source docx
files (see fix_transcription_issues.py / generate_transcription_report.py)
actually produce correct output HTML, without re-running the full,
heavier `script.py exec` pipeline (which also builds CIDOC-CRM graphs and
can re-download the docx from Google Docs if -gdoc is passed).

It reproduces exactly the steps script.py's exec() runs before it gets to
RDF graph creation: convert2vec -> _clean_vectors -> parse_pages ->
write vectors.json/pages.json/txt/html. Output text is therefore exactly
the docx text (the pipeline no longer inserts whitespace at runtime --
see assets/scripts/migrate_missing_whitespace.py for the source-side
equivalent, and assets/scripts/verify_output_matches_source.py to prove it).

Every generated page HTML is also copied (replacing any existing file of
the same name) into the live MB_Diaries-app mirror directory, the same
`<app_path>/file/<diary>_<page>.html` convention script.py's own exec() uses
-- pass --no-app-mirror to skip that and only write assets/output/.

Per-diary page-marker regex overrides are pulled from .vscode/launch.json
(only 1891-93 and 1902-03 have one; every other diary uses script.py's
built-in default).

Usage:
    python assets/scripts/regenerate_pages_html.py --all
    python assets/scripts/regenerate_pages_html.py --diary 1891-93
    python assets/scripts/regenerate_pages_html.py --all --no-app-mirror
"""

import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from assets.scripts import const, writer
from assets.scripts.convert import convert2vec

# Mirrors script.py's own module-level regex/clean_vectors/parse_pages/
# _fix_missing_whitespace so this stays in lockstep with the real pipeline
# without importing script.py itself (which eagerly loads the spaCy model
# at import time, even though NER is dormant).
import script as pipeline  # noqa: E402

# Same path script.py's exec() hardcodes for its app_path argument.
DEFAULT_APP_PATH = "/Users/gspinaci/projects/mb_diaries/apps/MB_Diaries-app"


def _regex_overrides_from_launch_json(path=".vscode/launch.json"):
  raw = open(path, encoding="utf-8").read()
  raw_no_comments = re.sub(r'^\s*//.*$', '', raw, flags=re.MULTILINE)
  data = json.loads(raw_no_comments)
  overrides = {}
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
    if diary and regex:
      overrides[diary] = regex
  return overrides


def regenerate(diary_stem, regex=None, app_path=DEFAULT_APP_PATH):
  cur_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  input_path = os.path.join(cur_path, "assets", "input", diary_stem.split("_")[0])
  output_path = os.path.join(cur_path, "assets", "output", diary_stem.split("_")[0])
  docx_path = os.path.join(input_path, f"{diary_stem}.docx")

  if not os.path.exists(docx_path):
    raise FileNotFoundError(docx_path)

  writer.create_dir(output_path)

  vec = convert2vec(docx_path)
  vec = pipeline._clean_vectors(vec, regex=regex)
  duplicate_pages = []
  pages = pipeline.parse_pages(vec[const.key_document], regex=regex, duplicate_report=duplicate_pages)
  pipeline._write_duplicate_page_report(duplicate_pages, input_path, diary_stem)

  writer.write_json(os.path.join(output_path, "vectors.json"), vec)
  writer.write_json(os.path.join(output_path, "pages.json"), pages)
  writer.write_pages(output_path, pages)
  writer.write_pages_html(output_path, pages, diary_stem, app_path=app_path)

  return len(pages), len(duplicate_pages)


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("--diary", help="Diary stem, e.g. 1934 or 1891-93")
  group.add_argument("--all", action="store_true", help="Regenerate every docx under assets/input")
  parser.add_argument("--no-app-mirror", action="store_true",
                       help="Don't copy generated HTML into the MB_Diaries-app file/ directory")
  parser.add_argument("--app-path", default=DEFAULT_APP_PATH,
                       help=f"Path to the MB_Diaries-app checkout (default: {DEFAULT_APP_PATH})")
  args = parser.parse_args()

  overrides = _regex_overrides_from_launch_json()
  app_path = None if args.no_app_mirror else args.app_path

  if args.diary:
    diary_stems = [args.diary]
  else:
    diary_stems = sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob("assets/input/*/*.docx")
    )

  for diary_stem in diary_stems:
    regex = overrides.get(diary_stem)
    try:
      n_pages, n_dupes = regenerate(diary_stem, regex=regex, app_path=app_path)
    except Exception as e:  # noqa: BLE001 - keep going, report failures at the end
      print(f"{diary_stem:12s} FAILED: {e}")
      continue
    regex_note = f" (regex override: {regex})" if regex else ""
    dupe_note = f"  [{n_dupes} duplicate marker(s) merged]" if n_dupes else ""
    print(f"{diary_stem:12s} {n_pages:4d} pages{regex_note}{dupe_note}")


if __name__ == "__main__":
  main()
