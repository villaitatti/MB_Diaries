from collections import OrderedDict
from spacy.lang.en import English
import dateutil.parser
import pandas as pd
import logging
import click
import spacy
import json
import re
import os
import requests
from docx import Document

from assets.scripts.convert import convert2vec
from assets.scripts import writer, upload, const, rdf
from assets.scripts.concatenate import concatenate_diary_pages

# Set up logging


nlp_allowed_types = ['PERSON', "ORG", "LOC"]

nlp = spacy.load('en_core_web_lg')

regex_date = re.compile(const.regex_date)
missing_whitespace_pattern = re.compile(r'(?<=\w)([.!?;,:])(?![A-Z]\.)(?=\w)')

def download_google_doc(file_id, output_path):
  download_url = f'https://docs.google.com/uc?export=download&id={file_id}'
  response = requests.get(download_url)
  
  if response.status_code == 200:
    with open(output_path, 'wb') as f:
      f.write(response.content)
    print(f'Downloaded document to {output_path}')
  else:
    print(f'Failed to download document. Status code: {response.status_code}')


def _clean_vectors(vectors):
  """
  Clean vectors by extracting page markers into separate objects.

  Args:
      vectors (list): List of document objects with text and runs.

  Returns:
      list: New list of vectors with page markers separated.
  """

  def _update_run_text(run, text):
    new_run = run.copy()  # Or use deepcopy if nested structures exist
    new_run[const.KEY_VALUE] = text
    return new_run
  
  def _clean_paragraph_leading_space(runs):
    """
    Remove leading whitespace from the first run in a paragraph.
    
    Args:
        runs (list): List of runs in a paragraph.
    
    Returns:
        list: Runs with leading whitespace removed from first run.
    """
    if runs and len(runs) > 0:
      # Remove leading whitespace from first run only
      first_run = runs[0].copy()
      first_run[const.KEY_VALUE] = first_run[const.KEY_VALUE].lstrip()
      runs[0] = first_run
    
    return runs

  new_vectors = []

  for vector in vectors[const.key_document]:
    new_vector = {}
    runs = vector[const.KEY_RUNS]
    
    for run in runs:
      text = run[const.KEY_VALUE]
      matches = list(re.finditer(const.regex_page_pattern, text, flags=re.MULTILINE))
      
      # If there is no match, add the current run to the vector
      if len(matches) == 0:
        new_vector[const.KEY_RUNS] = [] if const.KEY_RUNS not in new_vector else new_vector[const.KEY_RUNS]
        new_vector[const.KEY_RUNS].append(run)
      
      # Otherwise, split the text into multiple runs
      else:
        for match in matches:
          # add the text before to the current vector, with a run
          # and store the current vector
          before_text = text[:match.start()]
          if before_text:
            new_vector[const.KEY_RUNS] = [] if const.KEY_RUNS not in new_vector else new_vector[const.KEY_RUNS]
            new_vector[const.KEY_RUNS].append(_update_run_text(run, before_text))
            new_vectors.append(new_vector)
            new_vector = {}
            
          # case in which the page marker is the only text in the run

          # if there are other runs stored
          if const.KEY_RUNS in new_vector and len(new_vector[const.KEY_RUNS]) > 0:
            new_vectors.append(new_vector)
            new_vector = {}
          
          # Add the page marker to a new vector
          # and store the current vector
          match_text = text[match.start():match.end()]
          new_vector[const.KEY_RUNS] = [_update_run_text(run, match_text)]
          new_vectors.append(new_vector)
          new_vector = {}
          
          # Add the next text to the current vector
          # The next text should the text until the end of the current text or the start of the next page marker.
          # Do not store the current vector here, because it may be updated in the next iteration
          next_match_start = matches[matches.index(match) + 1].start() if matches.index(match) + 1 < len(matches) else len(text)
          after_text = text[match.end():min(len(text), next_match_start)]
          if after_text:
            new_vector[const.KEY_RUNS] = [] if const.KEY_RUNS not in new_vector else new_vector[const.KEY_RUNS]
            new_vector[const.KEY_RUNS].append(_update_run_text(run, after_text))

    # Store the current vector if it has not been stored yet
    if new_vector:
      new_vectors.append(new_vector)
      new_vector = {}
      

  # Clean leading whitespace from first run in each paragraph and update text
  for vector in new_vectors:
    if const.KEY_RUNS in vector:
      vector[const.KEY_RUNS] = _clean_paragraph_leading_space(vector[const.KEY_RUNS])
    vector[const.KEY_TEXT] = ''.join(run[const.KEY_VALUE] for run in vector[const.KEY_RUNS]).strip()

  return {const.key_document: new_vectors}


def _fix_missing_whitespace(pages):
  """
  Detect and fix missing whitespace after punctuation within page paragraphs.

  Args:
      pages (OrderedDict): Pages produced by parse_pages.

  Returns:
      tuple: (pages, log_entries) pages with fixes applied and log entries describing fixes.
  """

  log_entries = []

  for page_number, page in pages.items():
    page_updated = False
    paragraphs = page.get(const.key_paragraphs, [])

    for paragraph_index, paragraph in enumerate(paragraphs, start=1):
      runs = paragraph.get(const.KEY_RUNS, [])
      paragraph_updated = False

      for idx, run in enumerate(runs):
        value = run.get(const.KEY_VALUE, '')
        if not value:
          continue

        matches = list(missing_whitespace_pattern.finditer(value))
        if not matches:
          continue

        allowed_positions = set()
        for match in matches:
          pos = match.start()
          prev_char = value[pos - 1] if pos > 0 else ''
          next_char = value[pos + 1] if pos + 1 < len(value) else ''

          # Skip numeric decimals/timestamps like 9.20
          if prev_char.isdigit() and next_char.isdigit():
            continue

          allowed_positions.add(pos)

        if not allowed_positions:
          continue

        paragraph_updated = True
        page_updated = True
        original_value = value

        new_chars = []
        for char_index, char in enumerate(value):
          new_chars.append(char)
          if char_index in allowed_positions:
            # Insert a space unless already present
            if char_index + 1 < len(value) and value[char_index + 1] != ' ':
              new_chars.append(' ')

        new_value = ''.join(new_chars)

        # Update run with new value
        updated_run = run.copy()
        updated_run[const.KEY_VALUE] = new_value
        runs[idx] = updated_run

        # Record log entry for each allowed position
        for pos in allowed_positions:
          start = max(0, pos - 20)
          end = min(len(original_value), pos + 21)
          context = original_value[start:end].strip()
          log_entries.append({
              'page': page_number,
              'paragraph': paragraph_index,
              'context': context
          })

      if paragraph_updated:
        paragraph[const.KEY_RUNS] = runs
        paragraph[const.KEY_TEXT] = ''.join(run[const.KEY_VALUE] for run in runs).strip()

    if page_updated:
      page[const.key_paragraphs] = paragraphs
      page[const.key_text] = '\n'.join(p[const.KEY_TEXT] for p in paragraphs)

  return pages, log_entries


def _write_missing_whitespace_log(log_entries, output_path):
  """
  Write missing whitespace log entries to a file for manual review.

  Args:
      log_entries (list): Entries produced by _fix_missing_whitespace.
      output_path (str): Directory where the log file should be written.
  """

  log_path = os.path.join(output_path, 'missing_whitespace_report.log')

  with open(log_path, 'w', encoding='utf-8') as log_file:
    if not log_entries:
      log_file.write('No missing whitespace issues detected.\n')
      return

    log_file.write('Missing whitespace issues detected:\n')
    for entry in log_entries:
      log_file.write(
          f"Page {entry['page']}, Paragraph {entry['paragraph']}: {entry['context']}\n"
      )


def parse_pages(paragraphs, limit=-1, regex=None):

  def _get_page_index(paragraph):
    # Extract page index from the page marker
    page_marker = re.findall(page_pattern, paragraph)[0]
    page_index = int(page_index_pattern.findall(
      re.sub(const.regex_brackets, '', page_marker))[0])
    return page_index

  def _save_page(page_content, page_index):
    # Reverse page content order back to normal and store in pages
    page_content.reverse()
    pages[page_index] = {
        const.key_text: '\n'.join([p[const.key_text] for p in page_content]),
        const.key_paragraphs: page_content
    }

  if regex:
    page_pattern = regex
  else:
    page_pattern = r'\[p?0*\d{,3}\]'
  
  page_exact_pattern = rf'^{page_pattern}$'
  page_index_pattern = re.compile(r'\d+')
  pages = OrderedDict()
  page_content = []

  # Process paragraphs in reverse order
  for paragraph in reversed(paragraphs):
    if not paragraph[const.KEY_TEXT]:
      continue

    # Check if the paragraph is a page marker
    # E.G., "[0255]"
    if re.search(page_exact_pattern, paragraph[const.KEY_TEXT], flags=re.MULTILINE):

      page_index = _get_page_index(paragraph[const.KEY_TEXT])
      
      _save_page(page_content, page_index)
      page_content = []
      
    # Otherwise, add the paragraph to the current page
    else:
      page_content.append(paragraph)

  # Reverse pages back to original order and apply limit if needed
  pages = OrderedDict(reversed(pages.items()))
  if limit != -1:
    pages = OrderedDict(list(pages.items())[:limit])

  return pages


def parse_note_1903_serialize_type(type):
  if type == 'organization / group':
    return 'organization'
  elif type == 'visual art' or type == 'visual arts':
    return 'visual_art'
  else:
    return type


def parse_note_1903(row, pages):

  regex_page = re.compile(r'[\d]{3,}')

  # Parse pages
  entiy_page = row[const.note_header_page]
  entity_value = row[const.note_header_entity]
  entity_number = row[const.note_header_number]
  entity_type = row[const.note_header_type]
  authority = row[const.note_header_authority]
  note1 = row[const.note_header_descriptor]
  note2 = row[const.note_header_context]
  disambiguation1 = row[const.note_header_disambiguation1]
  disambiguation2 = row[const.note_header_disambiguation2]
  disambiguation3 = row[const.note_header_disambiguation3]

  disambiguations = [disambiguation1, disambiguation2, disambiguation3]

  text = entity_value if entity_value else note1

  if entiy_page:

    page_number = int(regex_page.findall(entiy_page)[-1])

    if page_number in pages:
      current_page = pages[page_number]

      for p in current_page[const.key_paragraphs]:
        if entity_value in p:
          return (entity_number, {
              const.key_footnote_header_page: page_number,
              const.footnote_type: parse_note_1903_serialize_type(entity_type),
              const.footnote_fulltext: text,
              const.footnote_permalinks: disambiguations,
              const.footnote_index: current_page[const.key_paragraphs].index(p) + 1,
              const.footnote_start: p.index(entity_value),
              const.footnote_end: p.index(
                  entity_value) + len(entity_value)
          })

  return None


def parse_note_generic(index, row, pages):
  entity_page = int(
      row[const.diaries['1891'][const.key_footnote_header_page]])
  entity_value = row[const.diaries['1891'][const.key_footnote_header_value]]
  entity_type = row[const.diaries['1891'][const.key_footnote_header_type]]

  try:
    entity_annotator = row[const.key_footnote_header_annotator]
  except Exception:
    entity_annotator = 'admin'

  note = None

  if entity_type == 'art':

    # Get the current page
    if entity_page in pages:
      current_page = pages[entity_page]

      # Check in each paragraph if it contains the entity
      for p in current_page[const.key_paragraphs]:
        start_index = p[const.key_text].lower().find(
            entity_value.lower())
        if start_index != -1:
          note = (index, {
              const.key_footnote_header_page: entity_page,
              const.footnote_type: entity_type,
              const.footnote_fulltext: entity_value,
              const.footnote_permalinks: [],
              const.footnote_index: current_page[const.key_paragraphs].index(p) + 1,
              const.footnote_start: start_index,
              const.footnote_end: start_index + len(entity_value),
              const.footnote_annotator: entity_annotator.lower()
          })
          break

  return note


def parse_note_1891(index, row, pages):

  entity_page = int(
      row[const.diaries['1891'][const.key_footnote_header_page]])

  entity_value = row[const.diaries['1891'][const.key_footnote_header_value]]
  entity_type = row[const.diaries['1891'][const.key_footnote_header_type]]
  entity_wikidata = row[const.diaries['1891']
                        [const.key_footnote_header_permalinks]]
  entity_annotator = row[const.diaries['1891']
                         [const.key_footnote_header_annotator]]

  permalinks = [
      f'https://www.wikidata.org/wiki/{entity_wikidata}'] if entity_wikidata else []

  if entity_page in pages:
    current_page = pages[entity_page]

    for p in current_page[const.key_paragraphs]:
      if entity_value in p:
        return (index, {
            const.key_footnote_header_page: entity_page,
            const.footnote_type: entity_type,
            const.footnote_fulltext: entity_value,
            const.footnote_annotator: entity_annotator.lower(),
            const.footnote_permalinks: permalinks,
            const.footnote_index: current_page[const.key_paragraphs].index(p) + 1,
            const.footnote_start: p.index(entity_value),
            const.footnote_end: p.index(
                entity_value) + len(entity_value)
        })

  return None


def parse_notes(pages, diary_notes, diary, limit=-1):

  parsed_notes = {}

  # Check if note file exists
  if os.path.exists(diary_notes):

    df_diary_notes = pd.read_csv(diary_notes)

    df_diary_notes.sort_values(
        by=const.diaries[diary][const.key_footnote_header_page], ascending=True, inplace=True)
    df_diary_notes.reset_index(drop=True, inplace=True)
    df_diary_notes.fillna('', inplace=True)

    for index, row in df_diary_notes.iterrows():

      if limit != -1 and index >= limit:
        break

      note_parsed = parse_note_generic(index, row, pages)

      try:
        note_parsed_id = note_parsed[0]
        note_parsed_body = note_parsed[1]
        parsed_notes[note_parsed_id] = note_parsed_body

      except Exception as e:
        print(e)
        continue

  # Execute NER if needed
  else:
    print('No notes file found. NER should be executed...')

  return parsed_notes


def check_cleaned(output_path):
  return os.path.exists(os.path.join(output_path, 'footnotes_cleaned.tsv'))


def parse_footnotes(pages, footnotes):

  elements = []

  # Link footnotes
  for key, page in pages.items():

    text = page[const.key_text]

    try:
      # Search if there are footnotes in pages
      for match in re.findall(const.regex_footnote_id, text):
        identifier = match.replace("----", "")

        before = text.split(match)[0]

        nlp_tokenizer = English()
        # Create a Tokenizer with the default settings for English
        # including punctuation rules and exceptions
        tokenizer = nlp_tokenizer.tokenizer

        tokens = tokenizer(before)

        if const.footnote_permalinks in footnotes[identifier]:
          element = [key, identifier, tokens[-4:], footnotes[identifier][const.footnote_fulltext],
                     footnotes[identifier][const.footnote_type], ', '.join(footnotes[identifier][const.footnote_permalinks])]
        else:
          element = [key, identifier, tokens[-4:], footnotes[identifier]
                     [const.footnote_fulltext], footnotes[identifier][const.footnote_type], '']

        elements.append(element)

    except Exception as ex:
      print(ex)

  return elements
def _write_concatenated_docx(concatenated_file, output_docx_path):
  """
  Create a DOCX document from a concatenated diary text file.

  Args:
      concatenated_file (str): Path to the concatenated text file.
      output_docx_path (str): Destination path for the generated DOCX.
  """

  if not concatenated_file or not os.path.exists(concatenated_file):
    print(f"Concatenated file not found: {concatenated_file}")
    return

  doc = Document()

  # Remove the default empty paragraph from a new document
  if doc.paragraphs:
    p = doc.paragraphs[0]._element
    p.getparent().remove(p)

  with open(concatenated_file, 'r', encoding='utf-8') as src:
    for line in src.read().splitlines():
      doc.add_paragraph(line.rstrip())

  os.makedirs(os.path.dirname(output_docx_path), exist_ok=True)
  doc.save(output_docx_path)
  print(f"Created DOCX: {output_docx_path}")



def parse_footnotes_cleaned(pages, footnotes):

  elements = {}

  for footnote_id, row in footnotes.iterrows():

    try:
      page_number = row[const.key_footnote_header_page]
      page = pages[page_number]
      text = row[const.key_footnote_header_before]
      paragraphs = page[const.key_paragraphs]
      footnote_id_complete = f'----{footnote_id}----'

      # get page and offset
      index = [idx for idx, s in enumerate(
          paragraphs) if footnote_id_complete in s][0]
      match = re.search(text.lower(), paragraphs[index].lower())

      elements[footnote_id] = {
          const.key_footnote_header_page: page_number,
          const.footnote_index: index,
          const.footnote_start: match.start(),
          const.footnote_end: match.end(),
          const.footnote_fulltext: paragraphs[index][match.start():match.end()],
          const.footnote_type: row[const.key_footnote_header_type],
          const.footnote_permalinks: row[const.key_footnote_header_permalinks].split(
              ', ')
      }

    except Exception as ex:
      print(f'Error with {footnote_id}: {ex}')
      continue

    # Remove footnote to handle subsequent offsets
    finally:
      re.sub(footnote_id_complete, '', paragraphs[index])

  return elements


def is_type_allowed(t):
  return t in nlp_allowed_types


def normalize_type(t):
  new_t = ""

  if t == "PERSON":
    new_t = "person"
  if t == "ORG" or t == "NORP":
    new_t = "organization"
  if t == "FAC" or t == "GPE" or t == "LOC":
    new_t = "location"
  if t == "DATE":
    new_t = "date"

  return new_t


def execute_ner(pages, name):

  data = {}
  i = 1
  for page_number, page in pages.items():
    ps = page["paragraphs"]
    for p in ps:

      doc = nlp(p)
      for ent in doc.ents:

        if is_type_allowed(ent.label_):
          data[i] = {
              const.key_footnote_header_page: page_number,
              const.footnote_fulltext: ent.text,
              const.footnote_index: ps.index(p) + 1,
              const.footnote_start: ent.start_char,
              const.footnote_end: ent.end_char,
              const.footnote_type: normalize_Type(ent.label_),
              const.footnote_permalinks: []
          }

          i += 1

  return data


def parse_days(df):
  # get days
  days = df['text'].str.contains(',[0-9]{4}$', na=False)

  df_out = df[days].copy()
  df_out['image_link'] = 'https://iiif.lib.harvard.edu/manifests/view/drs:493343177$' + \
      df_out["page"].astype(str) + 'i'
  df_out = df_out.rename(columns={'text': 'day_title'})

  df_out.to_csv(os.path.join(output_path, 'csv', 'metadata.csv'), columns=[
                'day', 'day_title', 'page', 'image_link'], index=False)


def parse_people(df):

  print(df.head())
  people = df['type'].str.fullmatch('PERSON')

  df_out = df[people].copy()
  df_out.to_csv(os.path.join(output_path, 'csv', 'people_extracted.csv'), columns=[
                'day', 'text', 'description', 'page', 'p', 'start', 'end'], index=False)


def update_days(df):
  df['day'] = df['text'].str.contains(',[0-9]{4}$', na=False).cumsum()
  return df


def parse_metadata(pages, diary, output_path, limit=-1):
  """
  Enhanced metadata parsing that extracts dates from HTML files using multiple patterns.
  
  Args:
      pages (dict): Dictionary of pages
      diary (str): Diary identifier
      output_path (str): Path to output directory
      limit (int): Limit for processing (-1 for no limit)
  
  Returns:
      dict: Updated pages with metadata
  """
  
  def is_valid_diary_date(parsed_date, diary_name):
    """
    Validate if a parsed date is reasonable for the given diary period.
    
    Args:
        parsed_date (datetime): The parsed date
        diary_name (str): The diary identifier (e.g., "1891-93", "1935")
    
    Returns:
        bool: True if the date is valid for this diary period
    """
    year = parsed_date.year
    
    # Extract expected year range from diary name
    if '-' in diary_name:
      # Handle ranges like "1891-93", "1896-98"
      start_year, end_year = diary_name.split('-')
      start_year = int(start_year)
      # Handle 2-digit end years
      if len(end_year) == 2:
        if int(end_year) < 50:  # Assume 00-49 means 20xx, 50-99 means 19xx
          end_year = int(f"20{end_year}")
        else:
          end_year = int(f"19{end_year}")
      else:
        end_year = int(end_year)
    else:
      # Handle single years like "1935"
      try:
        start_year = end_year = int(diary_name)
      except ValueError:
        # If we can't parse the diary name, use a broad historical range
        start_year, end_year = 1850, 1950
    
    # Allow some flexibility (±5 years) for diary periods
    return (start_year - 5) <= year <= (end_year + 5)
  
  # Define comprehensive date patterns
  date_patterns = [
    # Header dates: <h3>Tuesday, June 18, 1935, I Tatti</h3>
    r'<h3>([A-Za-z]+,?\s+[A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})',
    # Paragraph dates: Tuesday, Feb. 11, 1896, Villa Rosa, Fiesole
    r'<p>([A-Za-z]+,?\s+[A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})',
    # Short dates: 10 Jan. 1872
    r'<p>(\d{1,2}\s+[A-Za-z]+\.?\s+\d{4})',
    # European format: 20 Jan. 1876
    r'(\d{1,2}\s+[A-Za-z]+\.?\s+\d{4})',
    # Full format with day: Monday, April 24, 1933
    r'([A-Za-z]+,\s+[A-Za-z]+\s+\d{1,2},\s+\d{4})',
    # Abbreviated format: Apr. 23, 1907
    r'([A-Za-z]+\.?\s+\d{1,2},\s+\d{4})'
  ]
  
  html_path = os.path.join(output_path, 'html')
  
  # Process each page
  for page_number, page in pages.items():
    if limit != -1 and page_number > limit:
      break
      
    page_metadata = []
    
    # Try to read corresponding HTML file
    html_file = os.path.join(html_path, f'{diary}_{page_number}.html')
    if os.path.exists(html_file):
      try:
        with open(html_file, 'r', encoding='utf-8') as f:
          html_content = f.read()
          
        # Try each date pattern
        dates_found = []
        for pattern in date_patterns:
          matches = re.findall(pattern, html_content, re.IGNORECASE)
          for match in matches:
            # Clean up the match (remove HTML tags, extra spaces)
            clean_match = re.sub(r'<[^>]+>', '', match).strip()
            if clean_match and clean_match not in dates_found:
              dates_found.append(clean_match)
        
        # Parse found dates
        for date_text in dates_found:
          try:
            # Try to parse the date
            parsed_date = dateutil.parser.parse(date_text, fuzzy=True)
            
            # Validate the date is reasonable for this diary
            if is_valid_diary_date(parsed_date, diary):
              page_metadata.append({
                  const.key_object: parsed_date.strftime('%Y-%m-%d'),
                  const.key_predicate: const.key_note_header,
                  'original_text': date_text,
                  'confidence': 'high'
              })
              print(f"Found date in page {page_number}: {date_text} -> {parsed_date.strftime('%Y-%m-%d')}")
            else:
              print(f"Rejected invalid date for diary {diary} in page {page_number}: {date_text} -> {parsed_date.strftime('%Y-%m-%d')}")
              
          except (dateutil.parser.ParserError, ValueError) as ex:
            print(f"Could not parse date '{date_text}' in page {page_number}: {ex}")
            continue
            
      except Exception as ex:
        print(f"Error reading HTML file {html_file}: {ex}")
    
    # Fallback: try to parse dates from paragraph text (original method) with validation
    if not page_metadata:
      for paragraph in page[const.key_paragraphs]:
        try:
          parsed_date = dateutil.parser.parse(paragraph[const.key_text], fuzzy=True)
          
          # Validate the date is reasonable for this diary
          if is_valid_diary_date(parsed_date, diary):
            page_metadata.append({
                const.key_object: parsed_date.strftime('%Y-%m-%d'),
                const.key_predicate: const.key_note_header,
                'original_text': paragraph[const.key_text][:50] + '...',
                'confidence': 'medium'
            })
            print(f"Fallback date parsing for page {page_number}: {parsed_date.strftime('%Y-%m-%d')}")
            break  # Only take the first successful parse per page
          else:
            print(f"Rejected invalid fallback date for diary {diary} in page {page_number}: {parsed_date.strftime('%Y-%m-%d')}")
            
        except dateutil.parser.ParserError:
          continue

    # Store metadata if found
    if page_metadata:
      page[const.key_metadata] = page_metadata

  return pages


def ner(output_path):

  txt_path = os.path.join(output_path, 'txt')
  csv_path = os.path.join(output_path, 'csv')
  xlsx_path = os.path.join(output_path, 'xslx')

  ner_body = []

  for txt_file in os.listdir(txt_path):

    name_file = txt_file.replace('.txt', '')

    with open(os.path.join(txt_path, txt_file), 'r') as f:

      ner_body_curr = execute_ner(f.read(), name_file)
      ner_body.append(ner_body_curr)

      writer.write_csv(os.path.join(
          csv_path, f'{name_file}.csv'), ner_body_curr)
      writer.write_xlsx(os.path.join(
          xlsx_path, f'{name_file}.xlsx'), ner_body_curr)

def _check_number_pages(pages):
  highest_page = max(pages.keys())
  for i in range(highest_page):
    line = f'Page {i}'
    if i not in pages.keys():
      line += ' \t\tMISSING'
      logging.error(line)
    else:
      logging.debug(line)
    print(line)

@click.command()
@click.option('-d', 'diaries', required=True, multiple=True, help="Diaries to iterate. -d 1933 [-d 1933]")
@click.option('-u', 'exec_upload', is_flag=True, help="Execute the upload", default=False)
@click.option('-c', 'config', help="Type of connection in config.ini to use", default="localhost")
@click.option('-t', 'title', help="Name of the diary", default=None)
@click.option('-i', 'index', help="Index of the diary", default=None)
@click.option('-gdoc', 'google_doc', help="The Google Doc file ID", default=None)
@click.option('-iiif', 'iiif_manifest', help="URL of the IIIF Manifest", default=None)
@click.option('-r', 'regex', help="Regex pattern for pages", default=None)
@click.option('--concatenate', is_flag=True, default=False,
              help="Concatenate diary txt files into a single file with page markers.")
def exec(diaries, exec_upload, config, title, index, google_doc, iiif_manifest, regex, concatenate):
  cur_path = os.path.dirname(os.path.realpath(__file__))

  for diary in diaries:
    print(f'### Executing year {diary} ###')

    # Update default paths with specific
    input_path = os.path.join(cur_path, 'assets', 'input', diary)
    output_path = os.path.join(cur_path, 'assets', 'output', diary)
    docx_path = os.path.join(input_path, f'{diary}.docx')

    # Download the Google Doc ID is provided
    if google_doc:
      download_google_doc(google_doc, docx_path)
    
    os.makedirs(output_path, exist_ok=True)

    logging.basicConfig(filename=os.path.join(output_path, 'error.log'), level=logging.ERROR)

    manifest = json.load(
        open(os.path.join(input_path, f'{diary}.json')))

    # Check if output_path exists
    writer.create_dir(output_path)

    # Get text and footnote from a docx document
    vec = convert2vec(docx_path)

    # Clean vectors
    vec = _clean_vectors(vec)

    # Parse pages
    pages = parse_pages(vec[const.key_document], regex=regex)

    # Fix missing whitespace issues and log them
    pages, missing_whitespace_log = _fix_missing_whitespace(pages)
    _write_missing_whitespace_log(missing_whitespace_log, output_path)

    # Persist vectors after any cleanup
    writer.write_json(os.path.join(output_path, 'vectors.json'), vec)

    # check from 0 to len(pages) if there is a page missing
    _check_number_pages(pages)

    writer.write_json(os.path.join(output_path, 'pages.json'), pages)
    writer.write_pages(output_path, pages)
    writer.write_pages_html(output_path, pages, diary,
                            app_path='/Users/gspinaci/projects/mb_diaries/apps/MB_Diaries-app')

    # Create RDF Graphs for the diary
    diary_graphs = rdf.diary2graphs(
      diary, manifest, title, index, iiif_manifest)
    rdf.write_graphs(output_path, diary_graphs, 'diary')

    # Create RDF Graphs for the pages including metadata if any
    pages = parse_metadata(pages, diary, output_path)
    if concatenate:
      regex_pattern = regex if regex else r'\[p?0*\d{,3}\]'
      concatenation_outputs = concatenate_diary_pages(
          diary, pages, output_path, regex_pattern=regex_pattern)
      concatenated_file = concatenation_outputs.get('text_path') if concatenation_outputs else None
      if concatenated_file:
        output_docx_file = os.path.join(output_path, f'{diary}.docx')
        _write_concatenated_docx(concatenated_file, output_docx_file)
    writer.write_json(os.path.join(output_path, 'pages.json'), pages)
    pages_graphs = rdf.pages2graphs(diary, manifest, pages, output_path)
    rdf.write_graphs(output_path, pages_graphs, 'document')

    # diary_notes = os.path.join(input_path, const.key_notes_dir, f'{diary}.csv')
    # notes_parsed = parse_notes(pages, diary_notes, diary)
    # notes = rdf.footnotes2graphs(diary, notes_parsed)
    # rdf.write_graphs(output_path, notes, 'annotation')

  # Upload RDF graphs
  if exec_upload:
    upload.upload(output_path, diary, config)


if __name__ == '__main__':
  exec()
