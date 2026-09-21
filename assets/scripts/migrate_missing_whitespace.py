"""
Source-side migration of the ~1,118 "missing whitespace after punctuation"
sites that script.py used to insert at pipeline runtime (see
assets/scripts/const.py::regex_missing_whitespace_candidate). The runtime
fixer has been removed: output must equal source, so every legitimate site
is instead applied to the docx itself, as a tracked, reviewable change.

Unlike assets/scripts/fix_transcription_issues.py (one curated find/replace
per fix, must be globally unique), this tool works POSITIONALLY: it detects
every candidate site by regex against each paragraph's concatenated run
text, classifies it, and inserts a single space right after the punctuation
character at that exact offset -- never merging or reformatting anything
around it. It reuses fix_transcription_issues.py's run-offset machinery
(_paragraph_text_and_spans / _run_containing / _apply_replacement_in_paragraph)
and its write_changelog(), so the output is byte-compatible with what
generate_transcription_report.py already parses.

Site classes (see const.py for the exact regexes):
  AUTO           -- plain glued sentence boundary ("etc.Some" -> "etc. Some").
                    Applied automatically.
  REVIEW_INITIAL -- the left-hand token is a chain of single-letter initials
                    ("B.", "14.I"). Covers both real abbreviations ("M.me")
                    and real bugs ("Charles V.Packed") -- never auto-applied.
  REVIEW_DIGIT   -- a digit immediately follows the punctuation ("No.1",
                    "14.I.92"). Never auto-applied.
  (not a site)   -- blocked by the lowercase-abbreviation guard (e.g./i.e./
                    a.m./p.m./...) or the digit-digit decimal/time guard.

Two-phase workflow:

  1. Emit candidates (read-only, never opens the docx for writing):
       python assets/scripts/migrate_missing_whitespace.py --emit-candidates --all
     Writes assets/input/<diary>/<stem>_whitespace_sites.json (one record per
     AUTO/REVIEW site, "apply": true for AUTO, false for REVIEW -- flip
     specific REVIEW records to true after triage) and
     assets/input/<diary>/<stem>_whitespace_sites_blocked.md (evidence that
     the abbreviation sites were seen and deliberately left alone).

  2. Apply (always --dry-run first):
       python assets/scripts/migrate_missing_whitespace.py \
           --docx assets/input/1902-03/1902-03.docx \
           --sites assets/input/1902-03/1902-03_whitespace_sites.json \
           --out assets/input/1902-03/1902-03.docx \
           --changelog assets/input/1902-03/transcription_fixes_changelog_1902-03_batch2.md \
           --dry-run
     Re-validates every site against the LIVE docx before writing (still at
     the recorded offset, not already applied, still classified the same
     way), and refuses to save if any of const.forbidden_whitespace_results
     turns up in the result (a second, independent guard against ever
     writing a broken abbreviation into the docx).

     Re-running --apply on an already-migrated docx is a no-op: every site
     reports ALREADY_APPLIED, because the character after the punctuation is
     no longer a plain word character.

Standalone safety check, run after every --apply:
    python assets/scripts/migrate_missing_whitespace.py --check-forbidden --docx <path>

Sites files are single-use: applying one batch shifts the offsets recorded
for anything not yet applied in the same paragraph, so re-run
--emit-candidates before starting another batch.
"""

import argparse
import glob
import json
import os
import re
from datetime import datetime, timezone

from docx import Document

from assets.scripts import const
from assets.scripts.fix_transcription_issues import (
    _apply_replacement_in_paragraph,
    _iter_paragraphs,
    _paragraph_text_and_spans,
    write_changelog,
)

CANDIDATE_PATTERN = re.compile(const.regex_missing_whitespace_candidate)
LEFT_INITIAL_PATTERN = re.compile(const.regex_left_initial_chain)
MARKER_PATTERN = re.compile(const.regex_page_pattern)
DIGIT_PATTERN = re.compile(r'\d+')


def find_sites(text):
  """Yield (pos, cls, reason) for every whitespace-migration site in `text`.
  cls is one of AUTO / REVIEW_INITIAL / REVIEW_DIGIT. Sites blocked by the
  lowercase-abbreviation guard or the digit-digit decimal/time guard are not
  yielded at all."""
  for m in CANDIDATE_PATTERN.finditer(text):
    pos = m.start()
    prev_c = text[pos - 1] if pos > 0 else ''
    next_c = text[pos + 1] if pos + 1 < len(text) else ''
    if prev_c.isdigit() and next_c.isdigit():
      continue
    if next_c.isdigit():
      yield pos, 'REVIEW_DIGIT', 'a digit follows the punctuation'
    elif text[pos] == '.' and LEFT_INITIAL_PATTERN.search(text[:pos]):
      yield pos, 'REVIEW_INITIAL', 'left-hand token looks like an initial or abbreviation'
    else:
      yield pos, 'AUTO', None


def _page_markers(paragraph_texts, page_pattern):
  """List of (paragraph_index, offset, page_number) for every real page
  marker, in document order (offset is within that paragraph's text)."""
  markers = []
  for pi, text in enumerate(paragraph_texts):
    for m in MARKER_PATTERN.finditer(text):
      token = m.group(0)
      if re.fullmatch(page_pattern, token):
        digits = DIGIT_PATTERN.findall(re.sub(const.regex_brackets, '', token))
        if digits:
          markers.append((pi, m.start(), int(digits[0])))
  return markers


def _page_for(markers, paragraph_index, offset):
  page = None
  for pi, off, num in markers:
    if (pi, off) > (paragraph_index, offset):
      break
    page = num
  return page


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


def emit_candidates(diary_stem, input_dir):
  docx_path = os.path.join(input_dir, f"{diary_stem}.docx")
  document = Document(docx_path)
  paragraphs = list(_iter_paragraphs(document))
  texts = [p.text for p in paragraphs]
  page_pattern = _launch_json_page_pattern(diary_stem)
  markers = _page_markers(texts, page_pattern)

  sites = []
  blocked_count = 0
  blocked_samples = []
  site_id = 0
  for pi, text in enumerate(texts):
    for pos, cls, reason in find_sites(text):
      site_id += 1
      left = text[max(0, pos - 25):pos]
      right = text[pos + 1:pos + 26]
      punct = text[pos]
      find_window = text[max(0, pos - 15):pos + 16]
      replace_window = find_window[:pos - max(0, pos - 15)] + punct + ' ' + find_window[pos - max(0, pos - 15) + 1:]
      sites.append({
          "id": f"ws-{diary_stem}-{site_id:04d}",
          "class": cls,
          "apply": cls == "AUTO",
          "reason": reason,
          "paragraph_index": pi,
          "offset": pos,
          "punct": punct,
          "page": _page_for(markers, pi, pos),
          "left": left,
          "right": right,
          "find": find_window,
          "replace": replace_window,
          "note": f"missing space after {punct!r} ({cls})",
      })
  # Count blocked (abbreviation-guarded) sites for the evidence file: any
  # `.!?;,:` glued to a word char that find_sites() did NOT yield.
  old_style = re.compile(r'(?<=\w)([.!?;,:])(?=\w)')
  for pi, text in enumerate(texts):
    yielded = {pos for pos, _, _ in find_sites(text)}
    for m in old_style.finditer(text):
      pos = m.start()
      prev_c = text[pos - 1] if pos > 0 else ''
      next_c = text[pos + 1] if pos + 1 < len(text) else ''
      if prev_c.isdigit() and next_c.isdigit():
        continue
      if pos in yielded:
        continue
      blocked_count += 1
      if len(blocked_samples) < 40:
        blocked_samples.append(text[max(0, pos - 20):pos + 20])

  sites_path = os.path.join(input_dir, f"{diary_stem}_whitespace_sites.json")
  with open(sites_path, "w", encoding="utf-8") as f:
    json.dump(sites, f, ensure_ascii=False, indent=2)

  blocked_path = os.path.join(input_dir, f"{diary_stem}_whitespace_sites_blocked.md")
  with open(blocked_path, "w", encoding="utf-8") as f:
    f.write(f"# Blocked whitespace sites — {diary_stem}.docx\n\n")
    f.write(f"{blocked_count} site(s) matched a glued `.!?;,:` but were blocked by the "
            f"lowercase-abbreviation guard (`{const.regex_missing_whitespace_candidate}`). "
            f"Never applied, listed here only as evidence they were seen and deliberately "
            f"left alone.\n\n")
    for s in blocked_samples:
      f.write(f"- …{s}…\n")
    if blocked_count > len(blocked_samples):
      f.write(f"- … and {blocked_count - len(blocked_samples)} more\n")

  n_auto = sum(1 for s in sites if s["class"] == "AUTO")
  n_review = len(sites) - n_auto
  return sites_path, blocked_path, n_auto, n_review, blocked_count


def apply_sites(docx_path, sites_path, out_path, changelog_path, dry_run=False):
  with open(sites_path, encoding="utf-8") as f:
    sites = json.load(f)

  document = Document(docx_path)
  paragraphs = list(_iter_paragraphs(document))

  # Apply within each paragraph in descending offset order so an earlier
  # insertion never invalidates a later (lower-offset) one still pending.
  by_paragraph = {}
  for site in sites:
    by_paragraph.setdefault(site["paragraph_index"], []).append(site)

  # Snapshot of the touched paragraphs' text BEFORE any edits, so the
  # forbidden-string check below can tell "this migration just broke an
  # abbreviation" apart from "the manuscript already legitimately contains
  # this substring" (e.g. "(v. good)" is normal English, already correctly
  # spaced, and must not trip the guard).
  before_text = {pi: paragraphs[pi].text for pi in by_paragraph if pi < len(paragraphs)}

  results = []
  for pi, para_sites in by_paragraph.items():
    if pi >= len(paragraphs):
      for site in para_sites:
        results.append(_result(site, "SKIPPED_MISSING_PARAGRAPH"))
      continue
    paragraph = paragraphs[pi]
    for site in sorted(para_sites, key=lambda s: -s["offset"]):
      if not site.get("apply"):
        results.append(_result(site, "SKIPPED_REVIEW"))
        continue

      full_text, _spans = _paragraph_text_and_spans(paragraph)
      pos = site["offset"]
      if pos >= len(full_text) or full_text[pos] != site["punct"]:
        results.append(_result(site, "STALE_OFFSET"))
        continue
      next_c = full_text[pos + 1] if pos + 1 < len(full_text) else ''
      if not next_c or next_c.isspace():
        results.append(_result(site, "ALREADY_APPLIED"))
        continue

      # Re-classify against the LIVE text before writing anything.
      live_classes = {p: cls for p, cls, _ in find_sites(full_text)}
      if live_classes.get(pos) != site["class"]:
        results.append(_result(site, "RECLASSIFIED"))
        continue

      ok = _apply_replacement_in_paragraph(paragraph, pos, pos + 1, site["punct"] + " ")
      results.append(_result(site, "APPLIED" if ok else "FAILED_TO_APPLY"))

  # Post-condition: this migration must never newly introduce a broken
  # abbreviation. Only the paragraphs it touched are checked, and only
  # against their OWN before-text, so a paragraph that already legitimately
  # contains e.g. "(v. good)" doesn't trip the guard on text nobody edited.
  forbidden_hit = None
  for pi in by_paragraph:
    if pi >= len(paragraphs):
      continue
    after = paragraphs[pi].text
    before = before_text[pi]
    for bad in const.forbidden_whitespace_results:
      if bad in after and bad not in before:
        forbidden_hit = (bad, after)
        break
    if forbidden_hit:
      break

  if forbidden_hit:
    raise RuntimeError(
        f"Aborting, nothing saved: found forbidden string {forbidden_hit[0]!r} "
        f"in paragraph {forbidden_hit[1][:80]!r}"
    )

  if not dry_run:
    document.save(out_path)

  changelog_json_path = write_changelog(results, changelog_path, docx_path, sites_path)
  return results, changelog_json_path


def _result(site, status):
  return {
      "id": site["id"], "page": site.get("page"), "note": site["note"],
      "find": site["find"], "replace": site["replace"], "status": status,
  }


def check_forbidden(docx_path):
  document = Document(docx_path)
  hits = []
  for paragraph in _iter_paragraphs(document):
    for bad in const.forbidden_whitespace_results:
      if bad in paragraph.text:
        hits.append((bad, paragraph.text))
  return hits


def main():
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  mode = parser.add_mutually_exclusive_group(required=True)
  mode.add_argument("--emit-candidates", action="store_true")
  mode.add_argument("--apply", action="store_true")
  mode.add_argument("--check-forbidden", action="store_true")

  parser.add_argument("--diary", help="Diary stem, e.g. 1934 (with --emit-candidates)")
  parser.add_argument("--all", action="store_true", help="Every docx under assets/input (with --emit-candidates)")
  parser.add_argument("--docx", help="Path to the source .docx (with --apply / --check-forbidden)")
  parser.add_argument("--sites", help="Path to the *_whitespace_sites.json (with --apply)")
  parser.add_argument("--out", help="Path to write the corrected .docx (with --apply)")
  parser.add_argument("--changelog", help="Path to write the Markdown changelog (with --apply)")
  parser.add_argument("--dry-run", action="store_true")
  args = parser.parse_args()

  if args.emit_candidates:
    if args.diary:
      stems = [args.diary]
    elif args.all:
      stems = sorted(os.path.splitext(os.path.basename(p))[0]
                      for p in glob.glob("assets/input/*/*.docx"))
    else:
      parser.error("--emit-candidates requires --diary or --all")
    for stem in stems:
      input_dir = os.path.join("assets", "input", stem.split("_")[0])
      sites_path, blocked_path, n_auto, n_review, n_blocked = emit_candidates(stem, input_dir)
      print(f"{stem:12s} AUTO={n_auto:4d}  REVIEW={n_review:3d}  BLOCKED={n_blocked:3d}  -> {sites_path}")

  elif args.apply:
    if not (args.docx and args.sites and args.out and args.changelog):
      parser.error("--apply requires --docx --sites --out --changelog")
    results, changelog_json_path = apply_sites(
        args.docx, args.sites, args.out, args.changelog, dry_run=args.dry_run)
    applied = sum(1 for r in results if r["status"] == "APPLIED")
    print(f"Applied {applied}/{len(results)} sites.")
    for status in ("SKIPPED_REVIEW", "ALREADY_APPLIED", "STALE_OFFSET", "RECLASSIFIED",
                    "SKIPPED_MISSING_PARAGRAPH", "FAILED_TO_APPLY"):
      n = sum(1 for r in results if r["status"] == status)
      if n:
        print(f"  {status}: {n}")
    print(f"Changelog: {args.changelog}")
    print(f"Changelog (json): {changelog_json_path}")
    if not args.dry_run:
      print(f"Saved corrected docx: {args.out}")

  elif args.check_forbidden:
    if not args.docx:
      parser.error("--check-forbidden requires --docx")
    hits = check_forbidden(args.docx)
    if hits:
      print(f"FAIL: {len(hits)} forbidden string(s) found in {args.docx}")
      for bad, text in hits[:20]:
        print(f"  {bad!r} in: {text[:100]!r}")
      raise SystemExit(1)
    print(f"OK: no forbidden strings in {args.docx}")


if __name__ == "__main__":
  main()
