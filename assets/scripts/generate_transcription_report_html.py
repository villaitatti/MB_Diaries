"""
Generates one self-contained, human-readable HTML report per diary,
summarizing the transcription fixes made by fix_transcription_issues.py.

Everything for a given diary's transcription-fix work lives alongside its
source docx under assets/input/<diary>/: the `<stem>_fixes*.json` fix
definitions, the `transcription_fixes_changelog*.{md,json}` produced by
fix_transcription_issues.py, and the `transcription_fixes_report_<stem>.html`
this script writes. (The scan reports from scan_transcription_issues.py stay
under assets/output/<diary>/ -- those are a regenerable diagnostic, not a
fix record.)

For each diary it shows:
  - every fix actually applied, with a highlighted before/after example
  - every candidate that was reviewed and deliberately left alone (false
    positives, stylistic choices, editorial conventions, etc.), with the
    reasoning
  - a diary with no changelog at all (never scanned/touched) is skipped

Usage:
    python assets/scripts/generate_transcription_report_html.py --all
    python assets/scripts/generate_transcription_report_html.py --diary 1934
"""

import argparse
import glob
import html
import os
import re

APPLIED_ENTRY_RE = re.compile(
    r'^- \*\*(?P<id>[^\*]+)\*\*\s*(?P<page>p\.\S+\s*)?[—-]\s*(?P<note>.+)$'
)
FIND_REPLACE_RE = re.compile(r'`([^`]*)`\s*→\s*`([^`]*)`')
REVIEWED_ENTRY_RE = re.compile(r'^- \*\*(?P<label>[^\*]+)\*\*\s*(?P<rest>.*)$')


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
  exact = [
      p for p in all_md
      if re.search(r'_' + re.escape(diary_stem) + r'(?:\.md$|_batch\d+\.md$)', os.path.basename(p))
  ]
  return exact


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


KNOWN_SECTION_PREFIXES = ("Applied", "Skipped", "Reviewed, no fix needed")


def _extract_extra_sections(text):
  """Any '## ' section that isn't one of the three standard ones -- e.g.
  1891-93's "Not handled by this script" writeup -- kept verbatim so that
  richer per-diary notes aren't silently dropped."""
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


def _inline_md(text):
  text = html.escape(text)
  text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
  text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
  return text


def _mini_markdown_to_html(text):
  """Tiny paragraph/bullet-list renderer -- just enough for the free-form
  notes written into these changelogs, without a markdown dependency.
  Groups consecutive "- " lines into a <ul> regardless of blank-line
  separation (some of these changelogs run bullets back-to-back with no
  blank line between them), and everything else into <p> paragraphs."""
  html_parts = []
  paragraph_lines = []
  list_items = []

  def flush_paragraph():
    if paragraph_lines:
      html_parts.append(f"<p>{_inline_md(' '.join(paragraph_lines))}</p>")
      paragraph_lines.clear()

  def flush_list():
    if list_items:
      items = "".join(f"<li>{_inline_md(item)}</li>" for item in list_items)
      html_parts.append(f"<ul>{items}</ul>")
      list_items.clear()

  for raw_line in text.splitlines():
    line = raw_line.strip()
    is_indented_continuation = bool(raw_line[:1] in (" ", "\t")) and line and not line.startswith("- ")
    if not line:
      flush_paragraph()
      flush_list()
      continue
    if line.startswith("- "):
      flush_paragraph()
      list_items.append(line[2:])
    elif is_indented_continuation and list_items:
      # Wrapped continuation of the current bullet (indented, no blank
      # line yet, no new "- " marker) -- keep it part of the same item.
      list_items[-1] += " " + line
    else:
      flush_list()
      paragraph_lines.append(line)
  flush_paragraph()
  flush_list()
  return "\n".join(html_parts)


def _diff_spans(find, replace):
  """Highlight the differing middle of two similar strings by trimming a
  common prefix and suffix, so long shared context doesn't drown the actual
  change in the HTML output."""
  i = 0
  while i < len(find) and i < len(replace) and find[i] == replace[i]:
    i += 1
  j = 0
  while (j < len(find) - i and j < len(replace) - i and
         find[len(find) - 1 - j] == replace[len(replace) - 1 - j]):
    j += 1
  prefix = find[:i]
  find_mid = find[i:len(find) - j]
  replace_mid = replace[i:len(replace) - j]
  suffix = find[len(find) - j:] if j else ""
  return prefix, find_mid, replace_mid, suffix


def _render_pair_html(find, replace):
  prefix, find_mid, replace_mid, suffix = _diff_spans(find, replace)
  e = html.escape
  del_part = f'<del>{e(find_mid)}</del>' if find_mid else ""
  ins_part = f'<ins>{e(replace_mid)}</ins>' if replace_mid else ""
  before = f'{e(prefix)}{del_part}{e(suffix)}' if (find_mid or prefix or suffix) else e(find)
  after = f'{e(prefix)}{ins_part}{e(suffix)}' if (replace_mid or prefix or suffix) else e(replace)
  return before, after


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


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Transcription fixes — {diary}</title>
<style>
  :root {{
    --bg: #faf8f5; --fg: #2a2420; --muted: #766f66; --border: #e3ddd3;
    --card: #ffffff; --del-bg: #fbe7e7; --del-fg: #8a2b2b;
    --ins-bg: #e6f3e8; --ins-fg: #1e5c2f; --accent: #7a5230;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 2.5rem 1.25rem 4rem; background: var(--bg); color: var(--fg);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Georgia, serif;
    line-height: 1.5;
  }}
  .wrap {{ max-width: 880px; margin: 0 auto; }}
  h1 {{ font-size: 1.6rem; margin: 0 0 0.25rem; }}
  .subtitle {{ color: var(--muted); margin: 0 0 2rem; font-size: 0.95rem; }}
  .stats {{ display: flex; gap: 1.5rem; margin-bottom: 2.5rem; flex-wrap: wrap; }}
  .stat {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px;
           padding: 0.9rem 1.2rem; min-width: 120px; }}
  .stat .n {{ font-size: 1.6rem; font-weight: 600; }}
  .stat .l {{ font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }}
  h2 {{ font-size: 1.15rem; margin: 2rem 0 1rem; padding-bottom: 0.4rem; border-bottom: 1px solid var(--border); }}
  .fix {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px;
          padding: 1rem 1.25rem; margin-bottom: 0.9rem; }}
  .fix .meta {{ font-size: 0.8rem; color: var(--muted); margin-bottom: 0.5rem; }}
  .fix .meta code {{ background: none; color: var(--accent); font-weight: 600; }}
  .fix .note {{ margin-bottom: 0.6rem; }}
  .example {{ display: grid; grid-template-columns: 2.4rem 1fr; gap: 0.3rem 0.6rem; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.88rem; }}
  .example .tag {{ color: var(--muted); text-align: right; padding-top: 0.15rem; }}
  .example .line {{ background: #f4f1ec; border-radius: 6px; padding: 0.35rem 0.6rem; overflow-x: auto; white-space: pre-wrap; word-break: break-word; }}
  del {{ background: var(--del-bg); color: var(--del-fg); text-decoration: none; border-radius: 3px; padding: 0 0.1rem; }}
  ins {{ background: var(--ins-bg); color: var(--ins-fg); text-decoration: none; border-radius: 3px; padding: 0 0.1rem; font-weight: 600; }}
  .reviewed {{ background: var(--card); border: 1px solid var(--border); border-left: 4px solid #c9a35c;
               border-radius: 8px; padding: 0.7rem 1rem; margin-bottom: 0.6rem; font-size: 0.92rem; }}
  .reviewed .label {{ font-weight: 600; color: var(--accent); }}
  .empty {{ color: var(--muted); font-style: italic; }}
  .sources {{ margin-top: 3rem; font-size: 0.78rem; color: var(--muted); }}
  .sources code {{ background: #f0ece5; padding: 0.05rem 0.35rem; border-radius: 4px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Transcription fixes — {diary}</h1>
  <p class="subtitle">Source: <code>assets/input/{diary_dir}/{diary}.docx</code></p>

  <div class="stats">
    <div class="stat"><div class="n">{applied_count}</div><div class="l">Fixes applied</div></div>
    <div class="stat"><div class="n">{reviewed_count}</div><div class="l">Reviewed, no fix needed</div></div>
  </div>

  <h2>Fixes applied</h2>
  {applied_html}

  <h2>Reviewed, no fix needed</h2>
  {reviewed_html}

  {extra_sections_html}

  <div class="sources">Generated from: {sources}</div>
</div>
</body>
</html>
"""


def render_html(report):
  diary = report["diary"]
  diary_dir = diary.split("_")[0]

  if report["applied"]:
    parts = []
    for entry in report["applied"]:
      pairs_html = ""
      for find, replace in entry["pairs"]:
        before, after = _render_pair_html(find, replace)
        pairs_html += (
            f'<div class="example">'
            f'<div class="tag">before</div><div class="line">{before}</div>'
            f'<div class="tag">after</div><div class="line">{after}</div>'
            f'</div>'
        )
      if not pairs_html:
        pairs_html = '<p class="empty">(no example text captured)</p>'
      page_html = f'<code>{html.escape(entry["page"])}</code> ' if entry["page"] else ""
      parts.append(
          f'<div class="fix">'
          f'<div class="meta"><code>{html.escape(entry["id"])}</code> {page_html}'
          f'&mdash; {html.escape(entry["note"])}</div>'
          f'{pairs_html}'
          f'</div>'
      )
    applied_html = "\n".join(parts)
  else:
    applied_html = '<p class="empty">No fixes were needed for this diary.</p>'

  if report["reviewed"]:
    parts = []
    for entry in report["reviewed"]:
      parts.append(
          f'<div class="reviewed"><span class="label">{html.escape(entry["label"])}</span> '
          f'{html.escape(entry["body"])}</div>'
      )
    reviewed_html = "\n".join(parts)
  else:
    reviewed_html = '<p class="empty">Nothing needed manual review for this diary.</p>'

  sources = ", ".join(f'<code>{html.escape(os.path.basename(p))}</code>' for p in report["sources"])

  if report.get("extra_sections"):
    parts = []
    for title, body in report["extra_sections"]:
      parts.append(f"<h2>{html.escape(title)}</h2>\n{_mini_markdown_to_html(body)}")
    extra_sections_html = "\n".join(parts)
  else:
    extra_sections_html = ""

  return PAGE_TEMPLATE.format(
      diary=html.escape(diary),
      diary_dir=html.escape(diary_dir),
      applied_count=len(report["applied"]),
      reviewed_count=len(report["reviewed"]),
      applied_html=applied_html,
      reviewed_html=reviewed_html,
      extra_sections_html=extra_sections_html,
      sources=sources,
  )


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
    out_path = os.path.join(input_dir, f"transcription_fixes_report_{diary_stem}.html")
    with open(out_path, "w", encoding="utf-8") as f:
      f.write(render_html(report))
    print(f"{diary_stem:12s} applied={len(report['applied']):3d} "
          f"reviewed={len(report['reviewed']):3d} -> {out_path}")
    written += 1

  if skipped:
    print(f"\nSkipped (no changelog found): {', '.join(skipped)}")
  print(f"\nWrote {written} HTML report(s).")


if __name__ == "__main__":
  main()
