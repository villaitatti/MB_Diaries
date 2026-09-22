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


def _split_run_around(run, target):
  """Split `run` into before/target/after runs, all three keeping the original
  run's formatting, and return the middle run (the caller then restyles it).
  Returns None if `target` isn't in run.text."""
  text = run.text
  idx = text.find(target)
  if idx == -1:
    return None
  before, after = text[:idx], text[idx + len(target):]

  run.text = before
  r_element = run._r

  def _clone_empty(source_r):
    clone = copy.deepcopy(source_r)
    for t in clone.findall(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
      clone.remove(t)
    return clone

  mid_r = _clone_empty(r_element)
  mid_run = type(run)(mid_r, run._parent)
  mid_run.text = target
  r_element.addnext(mid_r)

  if after:
    after_r = _clone_empty(r_element)
    after_run = type(run)(after_r, run._parent)
    after_run.text = after
    mid_r.addnext(after_r)

  # An empty leftover run would still carry the original formatting and show
  # up as a stray <u><i></i></u> in the generated HTML.
  if not before:
    r_element.getparent().remove(r_element)
  return mid_run


def _apply_underline_in_run(run, target):
  """Split `run` so that the `target` substring (which must be a substring of
  run.text) becomes its own run with underline=True, preserving the rest of
  the run's formatting on the surrounding text."""
  mid_run = _split_run_around(run, target)
  if mid_run is None:
    return False
  mid_run.underline = True
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


_FORMAT_ATTRIBUTES = {
    "bold": "bold",
    "italic": "italic",
    "underline": "underline",
}


def _paragraph_full_text(paragraph):
  return _paragraph_text_and_spans(paragraph)[0]


def _find_unique_paragraph(document, predicate):
  matches = [p for p in _iter_paragraphs(document) if predicate(p)]
  if len(matches) != 1:
    return None, len(matches)
  return matches[0], 1


def _remove_paragraph(paragraph):
  element = paragraph._p
  element.getparent().remove(element)


def _join_with_next_paragraph(document, paragraph):
  """Append the following non-empty paragraph onto `paragraph`, dropping any
  blank paragraphs in between. Returns False if there is no paragraph left to
  join with."""
  # python-docx hands out a fresh Paragraph wrapper on every access, so the
  # position has to be found through the underlying XML element, not by
  # object equality.
  body_paragraphs = list(_iter_paragraphs(document))
  position = next((i for i, p in enumerate(body_paragraphs)
                   if p._p is paragraph._p), None)
  if position is None:
    return False

  to_drop = []
  following = None
  for candidate in body_paragraphs[position + 1:]:
    if _paragraph_full_text(candidate).strip():
      following = candidate
      break
    to_drop.append(candidate)

  if following is None:
    return False

  # Only insert a separator when the seam would otherwise glue two words
  # together -- the diaries' paragraphs often already carry a trailing space.
  head = _paragraph_full_text(paragraph)
  tail = _paragraph_full_text(following)
  if head and tail and not head[-1].isspace() and not tail[0].isspace():
    paragraph.add_run(" ")

  for run in list(following.runs):
    paragraph._p.append(run._r)

  for blank in to_drop:
    _remove_paragraph(blank)
  _remove_paragraph(following)
  return True


def _clear_run_format(run, remove):
  for flag in remove:
    attribute = _FORMAT_ATTRIBUTES.get(flag)
    if attribute is None:
      return False
    setattr(run, attribute, False)
  return True


def apply_structure_fixes(document, fixes):
  """Paragraph-level edits that a find/replace inside one paragraph can't make.

  Each fix is {id, op, note, page, ...} where `op` is one of:

    join_next        {anchor}          -- the paragraph containing `anchor` (once
                                         in the document) absorbs the next
                                         non-empty paragraph; the break is removed.
    delete_paragraph {text}            -- remove the paragraph whose whole
                                         (stripped) text equals `text`.
    clear_format     {context, target,
                      remove: [...]}   -- drop the named direct formatting
                                         ("bold"/"italic"/"underline") from
                                         `target` inside the paragraph containing
                                         `context`.

  Same contract as apply_fixes: an anchor that isn't found exactly once is
  reported and SKIPPED, never guessed.
  """
  results = []
  for fix in fixes:
    result = {
        "id": fix["id"], "page": fix.get("page"), "note": fix.get("note", ""),
    }
    op = fix["op"]

    if op == "join_next":
      anchor = fix["anchor"]
      result["find"] = anchor
      result["replace"] = "<join with next paragraph>"
      paragraph, count = _find_unique_paragraph(
          document, lambda p: anchor in _paragraph_full_text(p))
      if paragraph is None:
        result["status"] = "NOT_FOUND" if not count else "AMBIGUOUS"
        result["occurrences"] = count
      else:
        ok = _join_with_next_paragraph(document, paragraph)
        result["status"] = "APPLIED" if ok else "FAILED_TO_APPLY"

    elif op == "delete_paragraph":
      text = fix["text"]
      result["find"] = text
      result["replace"] = "<paragraph removed>"
      paragraph, count = _find_unique_paragraph(
          document, lambda p: _paragraph_full_text(p).strip() == text)
      if paragraph is None:
        result["status"] = "NOT_FOUND" if not count else "AMBIGUOUS"
        result["occurrences"] = count
      else:
        _remove_paragraph(paragraph)
        result["status"] = "APPLIED"

    elif op == "clear_format":
      context, target = fix["context"], fix["target"]
      remove = fix["remove"]
      result["find"] = target
      result["replace"] = f"<clear {'+'.join(remove)}>{target}</clear>"
      matches = []
      for paragraph in _iter_paragraphs(document):
        if context not in _paragraph_full_text(paragraph):
          continue
        for run in paragraph.runs:
          if target in run.text:
            matches.append(run)
      if len(matches) != 1:
        result["status"] = "NOT_FOUND" if not matches else "AMBIGUOUS"
        result["occurrences"] = len(matches)
      else:
        mid_run = _split_run_around(matches[0], target)
        ok = mid_run is not None and _clear_run_format(mid_run, remove)
        result["status"] = "APPLIED" if ok else "FAILED_TO_APPLY"

    else:
      result["find"] = op
      result["replace"] = ""
      result["status"] = "UNKNOWN_OP"

    results.append(result)
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
  parser.add_argument("--structure-fixes", help="Path to a JSON file with a list of {id,page,note,op,...} paragraph-level fixes (join_next / delete_paragraph / clear_format)")
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

  if args.structure_fixes:
    with open(args.structure_fixes, "r", encoding="utf-8") as f:
      structure_fixes = json.load(f)
    results += apply_structure_fixes(document, structure_fixes)

  if not args.dry_run:
    document.save(args.out)

  changelog_json_path = write_changelog(results, args.changelog, args.docx, args.fixes)

  applied = sum(1 for r in results if r["status"] == "APPLIED")
  print(f"Applied {applied}/{len(results)} fixes.")
  print(f"Changelog: {args.changelog}")
  print(f"Changelog (json): {changelog_json_path}")
  if not args.dry_run:
    print(f"Saved corrected docx: {args.out}")


if __name__ == "__main__":
  main()
