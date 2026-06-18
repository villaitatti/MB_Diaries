"""Utilities for concatenating diary pages into text and statistics."""

from __future__ import annotations

from collections import OrderedDict
from typing import Dict, List, Optional, Tuple
import os

from dateutil import parser

from . import const, writer


def _split_date_and_location(original_text: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
  """
  Split an original metadata string into a date-like portion and a location.

  Args:
      original_text: The raw text captured from the source document.

  Returns:
      Tuple where the first item represents the date text (if anything looks like a date)
      and the second item contains the trailing location string, when available.
  """

  if not original_text:
    return None, None

  segments = [segment.strip() for segment in original_text.split('.') if segment.strip()]
  if not segments:
    return original_text.strip(), None

  location_parts: List[str] = []
  date_parts: List[str] = segments[:]

  index = len(date_parts) - 1
  while index >= 0 and not any(char.isdigit() for char in date_parts[index]):
    location_parts.insert(0, date_parts.pop())
    index -= 1

  date_text = '. '.join(date_parts).strip() if date_parts else original_text.strip()
  location = '. '.join(location_parts).strip() if location_parts else None

  return date_text, location


def _build_date_headers(pages: "OrderedDict[int, Dict]") -> List[Dict]:
  """
  Build an ordered list of date headers derived from page metadata.

  Args:
      pages: Ordered dictionary of parsed page objects.

  Returns:
      List of dictionaries describing each detected date header.
  """

  headers: List[Dict] = []
  entry_counter = 1

  for page_number, page in pages.items():
    metadata_entries = page.get(const.key_metadata, []) or []

    for metadata in metadata_entries:
      original_text = metadata.get('original_text')
      date_iso = metadata.get(const.key_object)

      if not date_iso and original_text:
        try:
          parsed_date = parser.parse(original_text, fuzzy=True)
          date_iso = parsed_date.strftime('%Y-%m-%d')
        except (parser.ParserError, ValueError):
          date_iso = None

      date_text, location = _split_date_and_location(original_text)

      headers.append({
          "date": date_iso,
          "date_text": date_text,
          "location": location,
          "original_text": original_text,
          "page": page_number,
          "entry_number": entry_counter
      })
      entry_counter += 1

  return headers


def _write_concatenated_text(diary: str, pages: "OrderedDict[int, Dict]", output_path: str) -> str:
  """
  Persist the concatenated plain-text representation of the diary.

  Args:
      diary: Diary identifier.
      pages: Ordered dictionary of parsed page objects.
      output_path: Destination directory for output artifacts.

  Returns:
      Path to the written concatenated text file.
  """

  lines: List[str] = []

  for page_number, page in pages.items():
    lines.append(f"===[p{page_number}]===")
    page_text = page.get(const.key_text, "")
    if page_text:
      lines.extend(page_text.splitlines())

  concatenated_path = os.path.join(output_path, f"{diary}_concatenated.txt")
  os.makedirs(output_path, exist_ok=True)

  with open(concatenated_path, 'w', encoding='utf-8') as target:
    target.write('\n'.join(lines))

  return concatenated_path


def _write_concatenated_with_contexts(
    diary: str,
    pages: "OrderedDict[int, Dict]",
    output_path: str
) -> str:
  """Persist a concatenated representation that preserves paragraph contexts."""

  import re
  
  # Date pattern to detect date headers - matches various date formats
  date_pattern = re.compile(
      r'^\s*(?:'
      # Optional day of week: "Monday, " or "Sunday. "
      r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[,.\s]+)?'
      # Month: "Aug." or "August" or "Aug"
      r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
      # Optional period/space after month
      r'[.\s]*'
      # Day: "7" or "8"
      r'\d{1,2}'
      # Allow text in between (location names)
      r'.*?'
      # Year: "1891" or "91"
      r'(?:18|19|20)?\d{2}',
      re.IGNORECASE
  )

  lines: List[str] = []

  for page_number, page in pages.items():
    paragraphs = page.get(const.key_paragraphs, []) or []

    # Check if this page continues from previous page
    is_continuation = False
    if paragraphs:
      first_paragraph_text = (
          paragraphs[0].get(const.key_text)
          or paragraphs[0].get(const.KEY_TEXT)
          or ""
      ).strip()
      # A page is a continuation if the first paragraph starts with a lowercase letter
      if first_paragraph_text and first_paragraph_text[0].islower():
        is_continuation = True

    # Add page marker with CONT if needed
    if is_continuation:
      lines.append(f"===[p{page_number} CONT]===")
    else:
      lines.append(f"===[p{page_number}]===")

    if not paragraphs:
      # Fallback to the plain text if paragraphs are missing
      text = page.get(const.key_text, "")
      if text:
        lines.append(text)
      lines.append("")
      continue

    # Track if we've seen a date in this page
    seen_date_in_page = False
    
    # Add paragraphs without "[Paragraph X]" prefix
    for paragraph in paragraphs:
      paragraph_text = (
          paragraph.get(const.key_text)
          or paragraph.get(const.KEY_TEXT)
          or ""
      ).strip()
      
      if paragraph_text:
        # Check if this paragraph contains a date header
        if date_pattern.match(paragraph_text):
          # If we've already seen a date in this page, add a CONT marker
          if seen_date_in_page:
            lines.append(f"===[p{page_number} CONT]===")
          seen_date_in_page = True
        
        lines.append(paragraph_text)

    # Do not add metadata section
    lines.append("")

  contexts_path = os.path.join(output_path, f"{diary}_concatenated_with_conts.txt")
  os.makedirs(output_path, exist_ok=True)

  with open(contexts_path, 'w', encoding='utf-8') as target:
    target.write('\n'.join(lines).strip())

  return contexts_path


def concatenate_diary_pages(
    diary: str,
    pages: "OrderedDict[int, Dict]",
    output_path: str,
    regex_pattern: Optional[str] = None
) -> Dict[str, str]:
  """
  Concatenate diary pages into a single text file and produce statistics.

  Args:
      diary: Diary identifier.
      pages: Ordered dictionary of parsed page objects.
      output_path: Destination directory for output artifacts.
      regex_pattern: Currently unused but kept for backwards compatibility.

  Returns:
      Dictionary containing paths to the generated text, context and stats files.
  """

  if not isinstance(pages, OrderedDict):
    pages = OrderedDict(sorted(pages.items(), key=lambda item: item[0]))

  concatenated_path = _write_concatenated_text(diary, pages, output_path)
  contexts_path = _write_concatenated_with_contexts(diary, pages, output_path)

  sequence_numbers = list(pages.keys())
  stats = {
      "diary": diary,
      "total_sequences": len(sequence_numbers),
      "total_entries": 0,
      "first_sequence": sequence_numbers[0] if sequence_numbers else None,
      "last_sequence": sequence_numbers[-1] if sequence_numbers else None,
      "date_headers": []
  }

  date_headers = _build_date_headers(pages)
  stats["date_headers"] = date_headers
  stats["total_entries"] = len(date_headers)

  stats_path = os.path.join(output_path, f"{diary}_stats.json")
  writer.write_json(stats_path, stats)

  return {
      "text_path": concatenated_path,
      "contexts_path": contexts_path,
      "stats_path": stats_path
  }

