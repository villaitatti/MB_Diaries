"""
Per-diary manual-intervention steps applied to the source .docx BEFORE parsing.

Each step edits the docx in place and is idempotent, so it is safe to run after
every `-gdoc` download (which replaces the local docx with the Drive copy).
Register a diary's steps in PREPROCESS below.
"""
import json
import os
import re
import sys

from docx import Document

_WEEKDAY = r'(?:Mon|Tues?|Wed(?:nes)?|Thu(?:rs)?|Fri|Sat(?:ur)?|Sun)[a-z]*'
_MONTH = r'(?:Christmas|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
# A date header is a short standalone paragraph that opens with a weekday and
# names a month. shortcut: matches English weekday-first headers only, extend if
# another diary writes dates differently.
_HEADER = re.compile(rf'^\s*{_WEEKDAY}\b.*\b{_MONTH}', re.IGNORECASE)
_MAX_HEADER_LEN = 80


def underline_dates(docx_path):
  """Underline every date-header paragraph (the transcribers did not). Returns the list of paragraphs changed."""
  doc = Document(docx_path)
  changed = []
  for p in doc.paragraphs:
    text = p.text.strip()
    runs = [r for r in p.runs if r.text]
    if not (text and len(text) <= _MAX_HEADER_LEN and _HEADER.match(text) and runs):
      continue
    if all(r.underline for r in runs if r.text.strip()):
      continue
    for r in runs:
      r.underline = True
    changed.append(text)
  if changed:
    doc.save(docx_path)
    diary = os.path.splitext(os.path.basename(docx_path))[0]
    log = os.path.join(os.path.dirname(docx_path), f'transcription_fixes_changelog_{diary}_underline_dates.json')
    with open(log, 'w', encoding='utf-8') as f:
      json.dump([{'status': 'APPLIED', 'underline': t} for t in changed], f, indent=2, ensure_ascii=False)
  return changed


PREPROCESS = {
    '1898-99': [underline_dates],
}


def run(diary, docx_path):
  for step in PREPROCESS.get(diary, []):
    changed = step(docx_path)
    print(f'preprocess {step.__name__}: {len(changed)} change(s)')


if __name__ == '__main__':
  run(sys.argv[1], sys.argv[2])
