from collections import OrderedDict
from spacy.lang.en import English
import dateutil.parser
import pandas as pd
import json
import click
import spacy
import re
import sys
import os

# Add 'assets/scripts' to the system path
script_path = os.path.join(os.path.dirname(__file__), 'assets', 'scripts')
sys.path.append(script_path)

from convert import convert2vec
import writer
import upload
import const
import rdf


nlp_allowed_types = ['PERSON', "ORG", "LOC"]

nlp = spacy.load('en_core_web_lg')

regex_date = re.compile(const.regex_date)


def clean_footnotes(footnotes):
  dict_footnotes = {}

  for page_footnotes in footnotes:
    for footnote in page_footnotes:

      try:
        footnote_index = re.findall(const.regex_footnote, footnote)[0]
        full_text = re.sub(const.regex_footnote, "",
                           footnote).lower().replace(")\t", "").strip()

        # Create footnote
        dict_footnotes[footnote_index] = {
            const.footnote_fulltext: full_text
        }

        # If contains href
        href_matches = re.findall(const.regex_href, full_text)
        if href_matches:

          # Save the links in href attribute
          permalinks = [href[1] for href in href_matches]
          dict_footnotes[footnote_index][const.footnote_permalinks] = permalinks

          # If text contains Biblioteca Berenson
          if "biblioteca berenson" in full_text:
            dict_footnotes[footnote_index][const.footnote_type] = "Book"
          else:
            dict_footnotes[footnote_index][const.footnote_type] = "Person"

        else:
          dict_footnotes[footnote_index][const.footnote_type] = "Notes"

      except IndexError as ex:
        print(ex)
        continue

  return dict_footnotes


"""_summary_

Parse the pages of the diary and return a dictionary with the following structure:
{page_number: {text: <text>, content: [{text: <text>, type: <type>}, ... ]}

"""


def parse_pages(paragraphs, limit=-1):
  def _is_header(text):
    """Check if a text starts with the note header key, indicating a header."""
    return text.startswith(const.key_note_header)

  def _create_paragraph_container(text):
    """Encapsulate text as a header or paragraph."""
    text_type = const.key_header if _is_header(text) else const.key_paragraph
    clean_text = text.replace(const.key_note_header, '').strip(
    ) if _is_header(text) else text.strip()
    return {
        const.key_text: clean_text,
        const.key_type: text_type
    }

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

  page_pattern = r'\[p?\d+[^\]]*\]'
  page_exact_pattern = r'^\[p?\d+[^\]]*\]$'
  page_index_pattern = re.compile(r'\d+')
  pages = OrderedDict()
  page_content = []

  # Process paragraphs in reverse order
  for paragraph in reversed(paragraphs):
    if not paragraph:
      continue

    # Check if the paragraph is a page marker
    # E.G., "[0255]"
    if re.search(page_exact_pattern, paragraph, flags=re.MULTILINE):

      page_index = _get_page_index(paragraph)
      
      _save_page(page_content, page_index)
      page_content = []

    # check if the paragraph contains a page marker 
    # E.G., "Why should we put [0225] faithfulness above it?"
    elif re.search(page_pattern, paragraph, flags=re.MULTILINE):
      page_index = _get_page_index(paragraph)

      paragraph_splits = re.split(page_pattern, paragraph)
      
      page_content.append(_create_paragraph_container(paragraph_splits[1]))

      _save_page(page_content, page_index)
      page_content = []
      
      # Store the residual text
      page_content.append(_create_paragraph_container(paragraph_splits[0]))
      
    # Otherwise, add the paragraph to the current page
    else:
      page_content.append(_create_paragraph_container(paragraph))

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


def parse_metadata(pages, diary, limit=-1):

  # Search for headers stored in page paragraphs
  for index, page in pages.items():

    page_metadata = []
    for paragraph in page[const.key_paragraphs]:
      if paragraph[const.key_type] == 'h3':
        try:
          page_metadata.append({
              const.key_object: dateutil.parser.parse(paragraph[const.key_text], fuzzy=True).strftime('%Y-%m-%d'),
              const.key_predicate: const.key_note_header
          })
        except dateutil.parser.ParserError as ex:
          print(ex)
          continue

    if len(page_metadata) > 0 and const.key_metadata not in page[const.key_paragraphs]:
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


@click.command()
@click.option('-d', 'diaries', required=True, multiple=True, help="Diaries to iterate. -d 1933 [-d 1933]")
@click.option('-u', 'exec_upload', is_flag=True, help="Execute the upload", default=False)
@click.option('-c', 'config', help="Type of connection in config.ini to use", default="localhost")
@click.option('-t', 'title', help="Name of the diary", default=None)
@click.option('-i', 'index', help="Index of the diary", default=None)
@click.option('-iiif', 'iiif_manifest', help="URL of the IIIF Manifest", default=None)
def exec(diaries, exec_upload, config, title, index, iiif_manifest):
  cur_path = os.path.dirname(os.path.realpath(__file__))

  for diary in diaries:
    print(f'### Executing year {diary} ###')

    # Update default paths with specific
    input_path = os.path.join(cur_path, 'assets', 'input', diary)
    output_path = os.path.join(cur_path, 'assets', 'output', diary)

    manifest = json.load(
        open(os.path.join(input_path, f'{diary}.json')))

    # Check if output_path exists
    writer.create_dir(output_path)

    # Get text and footnote from a docx document
    vec = convert2vec(os.path.join(input_path, f'{diary}.docx'))

    # Parse and write page
    pages = parse_pages(vec[const.key_document])
    writer.write_json(os.path.join(output_path, 'pages.json'), pages)
    writer.write_pages(output_path, pages)
    writer.write_pages_html(output_path, pages, diary,
                            app_path='/Users/gspinaci/projects/mb_diaries/apps/MB_Diaries-app')

    # Create RDF Graphs for the diary
    diary_graphs = rdf.diary2graphs(
      diary, manifest, title, index, iiif_manifest)
    rdf.write_graphs(output_path, diary_graphs, 'diary')

    # Create RDF Graphs for the pages including metadata if any
    pages = parse_metadata(pages, diary)
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
