"""
Maintenance tool to apply targeted, tracked text corrections to a diary .docx
transcription.

Each "fix" is a small, surgical find/replace anchored to a literal substring
that must appear EXACTLY ONCE in the whole document. This is deliberately
conservative: if the anchor text is not found, or is found more than once,
the fix is SKIPPED (not guessed) and reported, so nothing is silently
mis-applied.

Edits are applied at the python-docx *run* level (not by replacing whole
paragraph text) so existing bold/italic/underline formatting on untouched
text is preserved. When a match spans multiple runs, the runs it spans are
merged into the first one.

Usage:
    python assets/scripts/fix_transcription_issues.py \
        --docx assets/input/1891-93/1891-93.docx \
        --fixes assets/input/1891-93/1891-93_fixes.json \
        --out assets/input/1891-93/1891-93.docx \
        --changelog assets/input/1891-93/transcription_fixes_changelog.md

The fixes JSON and the changelog both live alongside the diary's own docx
under assets/input/<diary>/, not under assets/scripts/ or assets/output/ --
everything about what was changed in a given diary's transcription stays
with that diary.

Every run writes a JSON changelog (machine-readable) next to the requested
--changelog path (same name, .json extension) plus the human-readable
Markdown report.
"""

import argparse
import copy
import json
import os
from datetime import datetime, timezone

from docx import Document


def _paragraph_text_and_spans(paragraph):
  """Return (full_text, spans) where spans is a list of (run_index, start, end)
  giving the character range each run occupies in full_text."""
  spans = []
  full_text = []
  pos = 0
  for i, run in enumerate(paragraph.runs):
    t = run.text or ""
    spans.append((i, pos, pos + len(t)))
    full_text.append(t)
    pos += len(t)
  return "".join(full_text), spans


def _run_containing(spans, offset):
  for i, start, end in spans:
    if start <= offset < end:
      return i, start, end
    # zero-length run or offset exactly at end of last run
  if spans and offset == spans[-1][2]:
    return spans[-1]
  return None


def _apply_replacement_in_paragraph(paragraph, match_start, match_end, replacement):
  full_text, spans = _paragraph_text_and_spans(paragraph)
  start_info = _run_containing(spans, match_start)
  end_info = _run_containing(spans, max(match_end - 1, match_start))
  if start_info is None or end_info is None:
    return False

  start_run_idx, start_run_start, _ = start_info
  end_run_idx, end_run_start, _ = end_info

  runs = paragraph.runs
  prefix = runs[start_run_idx].text[: match_start - start_run_start]
  suffix = runs[end_run_idx].text[match_end - end_run_start:]

  if start_run_idx == end_run_idx:
    runs[start_run_idx].text = prefix + replacement + suffix
  else:
    runs[start_run_idx].text = prefix + replacement
    runs[end_run_idx].text = suffix
    for i in range(start_run_idx + 1, end_run_idx):
      runs[i].text = ""
  return True


def _apply_underline_in_run(run, target):
  """Split `run` so that the `target` substring (which must be a substring of
  run.text) becomes its own run with underline=True, preserving the rest of
  the run's formatting on the surrounding text."""
  text = run.text
  idx = text.find(target)
  if idx == -1:
    return False
  before, after = text[:idx], text[idx + len(target):]

  run.text = before
  r_element = run._r

  mid_r = copy.deepcopy(r_element)
  for t in mid_r.findall(
      "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
    mid_r.remove(t)
  mid_run = type(run)(mid_r, run._parent)
  mid_run.text = target
  mid_run.underline = True
  r_element.addnext(mid_r)

  after_r = copy.deepcopy(r_element)
  for t in after_r.findall(
      "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
    after_r.remove(t)
  after_run = type(run)(after_r, run._parent)
  after_run.text = after
  mid_r.addnext(after_r)
  return True


def apply_underline_fixes(document, fixes):
  results = []
  for fix in fixes:
    fid = fix["id"]
    context = fix["context"]
    target = fix["target"]
    note = fix.get("note", "")
    page = fix.get("page")

    matches = []
    for paragraph in _iter_paragraphs(document):
      if context in paragraph.text:
        for run in paragraph.runs:
          if target in run.text and context in paragraph.text:
            matches.append(run)

    if len(matches) != 1:
      results.append({
          "id": fid, "page": page, "note": note, "find": target,
          "replace": f"<underline>{target}</underline>",
          "status": "NOT_FOUND" if not matches else "AMBIGUOUS",
          "occurrences": len(matches),
      })
      continue

    ok = _apply_underline_in_run(matches[0], target)
    results.append({
        "id": fid, "page": page, "note": note, "find": target,
        "replace": f"<underline>{target}</underline>",
        "status": "APPLIED" if ok else "FAILED_TO_APPLY",
    })
  return results


def _iter_paragraphs(document):
  # Only body paragraphs; the diaries under test don't use tables for prose,
  # but this keeps the door open without silently skipping table text.
  for paragraph in document.paragraphs:
    yield paragraph
  for table in document.tables:
    for row in table.rows:
      for cell in row.cells:
        for paragraph in cell.paragraphs:
          yield paragraph


def apply_fixes(document, fixes):
  """fixes: list of dicts with keys id, note, find, replace (and optional page).

  Returns list of result dicts (one per fix) describing what happened.
  """
  results = []
  for fix in fixes:
    fid = fix["id"]
    find = fix["find"]
    replace = fix["replace"]
    note = fix.get("note", "")
    page = fix.get("page")

    matches = []  # (paragraph, start, end)
    for paragraph in _iter_paragraphs(document):
      full_text, _spans = _paragraph_text_and_spans(paragraph)
      start = 0
      while True:
        idx = full_text.find(find, start)
        if idx == -1:
          break
        matches.append((paragraph, idx, idx + len(find)))
        start = idx + 1

    if len(matches) == 0:
      results.append({
          "id": fid, "page": page, "note": note, "find": find,
          "replace": replace, "status": "NOT_FOUND",
      })
      continue
    if len(matches) > 1:
      results.append({
          "id": fid, "page": page, "note": note, "find": find,
          "replace": replace, "status": "AMBIGUOUS",
          "occurrences": len(matches),
      })
      continue

    paragraph, start, end = matches[0]
    ok = _apply_replacement_in_paragraph(paragraph, start, end, replace)
    results.append({
        "id": fid, "page": page, "note": note, "find": find,
        "replace": replace,
        "status": "APPLIED" if ok else "FAILED_TO_APPLY",
    })
  return results


def write_changelog(results, changelog_md_path, docx_path, fixes_path):
  changelog_json_path = os.path.splitext(changelog_md_path)[0] + ".json"
  applied = [r for r in results if r["status"] == "APPLIED"]
  skipped = [r for r in results if r["status"] != "APPLIED"]

  os.makedirs(os.path.dirname(changelog_md_path), exist_ok=True)
  with open(changelog_json_path, "w", encoding="utf-8") as f:
    json.dump({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "docx": docx_path,
        "fixes_file": fixes_path,
        "results": results,
    }, f, ensure_ascii=False, indent=2)

  lines = [
      f"# Transcription fix log — {os.path.basename(docx_path)}",
      "",
      f"Generated: {datetime.now(timezone.utc).isoformat()}",
      f"Fixes definition: `{fixes_path}`",
      "",
      f"## Applied ({len(applied)})",
      "",
  ]
  for r in applied:
    page = f"p.{r['page']} " if r.get("page") else ""
    lines.append(f"- **{r['id']}** {page}— {r['note']}")
    lines.append(f"  - `{r['find']}` → `{r['replace']}`")
  lines += ["", f"## Skipped / needs manual review ({len(skipped)})", ""]
  for r in skipped:
    page = f"p.{r['page']} " if r.get("page") else ""
    extra = f" (occurrences={r['occurrences']})" if "occurrences" in r else ""
    lines.append(f"- **{r['id']}** {page}— {r['status']}{extra}: {r['note']}")
    lines.append(f"  - looked for: `{r['find']}`")
  with open(changelog_md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

  return changelog_json_path


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--docx", required=True, help="Path to the source .docx")
  parser.add_argument("--fixes", required=True, help="Path to a JSON file with a list of fixes")
  parser.add_argument("--underline-fixes", help="Path to a JSON file with a list of {id,page,note,context,target} underline fixes")
  parser.add_argument("--out", required=True, help="Path to write the corrected .docx")
  parser.add_argument("--changelog", required=True, help="Path to write the Markdown changelog")
  parser.add_argument("--dry-run", action="store_true", help="Report what would happen, don't write the docx")
  args = parser.parse_args()

  with open(args.fixes, "r", encoding="utf-8") as f:
    fixes = json.load(f)

  document = Document(args.docx)
  results = apply_fixes(document, fixes)

  if args.underline_fixes:
    with open(args.underline_fixes, "r", encoding="utf-8") as f:
      underline_fixes = json.load(f)
    results += apply_underline_fixes(document, underline_fixes)

  if not args.dry_run:
    document.save(args.out)

  changelog_json_path = write_changelog(results, args.changelog, args.docx, args.fixes)

  applied = sum(1 for r in results if r["status"] == "APPLIED")
  print(f"Applied {applied}/{len(fixes)} fixes.")
  print(f"Changelog: {args.changelog}")
  print(f"Changelog (json): {changelog_json_path}")
  if not args.dry_run:
    print(f"Saved corrected docx: {args.out}")


if __name__ == "__main__":
  main()
