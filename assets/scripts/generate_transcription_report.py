"""
Generates one human-readable Markdown report per diary, summarizing the
transcription fixes made by fix_transcription_issues.py. Plain Markdown
(not HTML) so the report renders directly in GitHub/GitLab's web UI, no
download or local server needed to "see" it.

Everything for a given diary's transcription-fix work lives alongside its
source docx under assets/input/<diary>/: the `<stem>_fixes*.json` fix
definitions, the `transcription_fixes_changelog*.{md,json}` produced by
fix_transcription_issues.py, and the `transcription_fixes_report_<stem>.md`
this script writes. (The scan reports from scan_transcription_issues.py stay
under assets/output/<diary>/ -- those are a regenerable diagnostic, not a
fix record.)

For each diary it shows:
  - every fix actually applied, with a before/after example as a fenced
    ```diff block (renders with red/green highlighting on GitHub)
  - every candidate that was reviewed and deliberately left alone (false
    positives, stylistic choices, editorial conventions, etc.), with the
    reasoning
  - any additional free-form sections from the changelog (e.g. 1891-93's
    "Not handled by this script" writeup), included verbatim
  - a diary with no changelog at all (never scanned/touched) is skipped

Usage:
    python assets/scripts/generate_transcription_report.py --all
    python assets/scripts/generate_transcription_report.py --diary 1934
"""

import argparse
import glob
import os
import re

APPLIED_ENTRY_RE = re.compile(
    r'^- \*\*(?P<id>[^\*]+)\*\*\s*(?P<page>p\.\S+\s*)?[—-]\s*(?P<note>.+)$'
)
FIND_REPLACE_RE = re.compile(r'`([^`]*)`\s*→\s*`([^`]*)`')
REVIEWED_ENTRY_RE = re.compile(r'^- \*\*(?P<label>[^\*]+)\*\*\s*(?P<rest>.*)$')

KNOWN_SECTION_PREFIXES = ("Applied", "Skipped", "Reviewed, no fix needed")


def _find_changelog_files(diary_stem, input_dir):
  """Return the changelog .md files that belong to this diary, in order."""
  all_md = sorted(glob.glob(os.path.join(input_dir, "transcription_fixes_changelog*.md")))
  docx_stems_in_dir = {
      os.path.splitext(os.path.basename(p))[0]
      for p in glob.glob(os.path.join(input_dir, "*.docx"))
  }
  if len(docx_stems_in_dir) <= 1:
    return all_md
  # Multiple diaries share this output dir (e.g. 1891 / 1891_old): only take
  # files explicitly suffixed with this exact diary stem as a whole token
  # (e.g. "..._1891_old.md" for stem "1891_old"), never a mere substring
  # match (stem "1891" must NOT also match "..._1891_old.md").
  return [
      p for p in all_md
      if re.search(r'_' + re.escape(diary_stem) + r'(?:\.md$|_batch\d+\.md$)', os.path.basename(p))
  ]


def _split_section(text, heading_prefix):
  """Return the body text of the first '## <heading_prefix...' section."""
  lines = text.splitlines()
  start = None
  for i, line in enumerate(lines):
    if line.startswith("## ") and line[3:].strip().startswith(heading_prefix):
      start = i + 1
      break
  if start is None:
    return ""
  end = len(lines)
  for i in range(start, len(lines)):
    if lines[i].startswith("## "):
      end = i
      break
  return "\n".join(lines[start:end]).strip()


def _parse_applied(section_text):
  entries = []
  blocks = re.split(r'\n(?=- \*\*)', section_text.strip())
  for block in blocks:
    block = block.strip()
    if not block:
      continue
    m = APPLIED_ENTRY_RE.match(block.splitlines()[0])
    if not m:
      continue
    pairs = FIND_REPLACE_RE.findall(block)
    entries.append({
        "id": m.group("id").strip(),
        "page": (m.group("page") or "").strip(),
        "note": m.group("note").strip(),
        "pairs": pairs,
    })
  return entries


def _parse_reviewed(section_text):
  entries = []
  blocks = re.split(r'\n(?=- \*\*)', section_text.strip())
  for block in blocks:
    block = block.strip()
    if not block:
      continue
    first_line = block.splitlines()[0]
    m = REVIEWED_ENTRY_RE.match(first_line)
    if not m:
      continue
    rest_lines = [m.group("rest").strip()] + [l.strip() for l in block.splitlines()[1:]]
    body = " ".join(l for l in rest_lines if l)
    entries.append({"label": m.group("label").strip(), "body": body})
  return entries


def _extract_extra_sections(text):
  """Any '## ' section that isn't one of the three standard ones -- e.g.
  1891-93's "Not handled by this script" writeup -- kept verbatim (it's
  already Markdown) so richer per-diary notes aren't silently dropped."""
  lines = text.splitlines()
  sections = []
  i = 0
  while i < len(lines):
    if lines[i].startswith("## "):
      title = lines[i][3:].strip()
      if not any(title.startswith(p) for p in KNOWN_SECTION_PREFIXES):
        j = i + 1
        while j < len(lines) and not lines[j].startswith("## "):
          j += 1
        body = "\n".join(lines[i + 1:j]).strip()
        if body:
          sections.append((title, body))
        i = j
        continue
    i += 1
  return sections


def build_diary_report(diary_stem, input_dir):
  md_files = _find_changelog_files(diary_stem, input_dir)
  if not md_files:
    return None

  applied = []
  reviewed = []
  extra_sections = []
  for path in md_files:
    with open(path, encoding="utf-8") as f:
      text = f.read()
    applied.extend(_parse_applied(_split_section(text, "Applied")))
    reviewed.extend(_parse_reviewed(_split_section(text, "Reviewed, no fix needed")))
    extra_sections.extend(_extract_extra_sections(text))

  return {"diary": diary_stem, "applied": applied, "reviewed": reviewed,
          "extra_sections": extra_sections, "sources": md_files}


def _diff_block(find, replace):
  """A fenced ```diff block -- GitHub/GitLab render '-' lines red and '+'
  lines green automatically, no CSS needed. Handles the rare multi-line
  find/replace by prefixing every line."""
  minus = "\n".join(f"- {line}" for line in find.splitlines() or [""])
  plus = "\n".join(f"+ {line}" for line in replace.splitlines() or [""])
  return f"```diff\n{minus}\n{plus}\n```"


def render_markdown(report):
  diary = report["diary"]
  diary_dir = diary.split("_")[0]
  lines = [
      f"# Transcription fixes — {diary}",
      "",
      f"Source: `assets/input/{diary_dir}/{diary}.docx`",
      "",
      f"**{len(report['applied'])}** fixes applied · "
      f"**{len(report['reviewed'])}** reviewed, no fix needed",
      "",
      "## Fixes applied",
      "",
  ]

  if report["applied"]:
    for entry in report["applied"]:
      page = f" `{entry['page']}`" if entry["page"] else ""
      lines.append(f"### `{entry['id']}`{page} — {entry['note']}")
      lines.append("")
      if entry["pairs"]:
        for find, replace in entry["pairs"]:
          lines.append(_diff_block(find, replace))
          lines.append("")
      else:
        lines.append("_(no example text captured)_")
        lines.append("")
  else:
    lines.append("_No fixes were needed for this diary._")
    lines.append("")

  lines.append("## Reviewed, no fix needed")
  lines.append("")
  if report["reviewed"]:
    for entry in report["reviewed"]:
      lines.append(f"- **{entry['label']}** {entry['body']}")
  else:
    lines.append("_Nothing needed manual review for this diary._")
  lines.append("")

  for title, body in report.get("extra_sections", []):
    lines.append(f"## {title}")
    lines.append("")
    lines.append(body)
    lines.append("")

  sources = ", ".join(f"`{os.path.basename(p)}`" for p in report["sources"])
  lines.append("---")
  lines.append(f"Generated from: {sources}")

  return "\n".join(lines) + "\n"


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("--diary", help="Diary stem, e.g. 1934 or 1891_old")
  group.add_argument("--all", action="store_true", help="Generate for every docx under assets/input")
  args = parser.parse_args()

  if args.diary:
    diary_stems = [args.diary]
  else:
    diary_stems = sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob("assets/input/*/*.docx")
    )

  written = 0
  skipped = []
  for diary_stem in diary_stems:
    input_dir = os.path.join("assets", "input", diary_stem.split("_")[0])
    report = build_diary_report(diary_stem, input_dir)
    if report is None:
      skipped.append(diary_stem)
      continue
    out_path = os.path.join(input_dir, f"transcription_fixes_report_{diary_stem}.md")
    with open(out_path, "w", encoding="utf-8") as f:
      f.write(render_markdown(report))
    print(f"{diary_stem:12s} applied={len(report['applied']):3d} "
          f"reviewed={len(report['reviewed']):3d} -> {out_path}")
    written += 1

  if skipped:
    print(f"\nSkipped (no changelog found): {', '.join(skipped)}")
  print(f"\nWrote {written} Markdown report(s).")


if __name__ == "__main__":
  main()
