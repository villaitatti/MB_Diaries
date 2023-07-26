# Import the local scripts
import sys
sys.path.append('./assets/scripts')

from spacy.lang.en import English
from asyncore import write
from collections import OrderedDict
import os
import re
import spacy
import pandas as pd
import numpy as np
import click
import rdf
import const
import upload
import writer

from convert import convert2text, convert2xml, convert2vec

nlp_allowed_types = ['PERSON', "ORG", "LOC"]

nlp = spacy.load('en_core_web_lg')


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


def parse_pages(paragraphs, diary, l=-1):

  def clear_data(p):

    # Remove tabs
    p = p.replace(r"\t", '')

    # Remove head and trail spaces
    p = p.strip()

    return p

  page_start_regex = const.diary_data[diary][const.key_page_regex_check]
  page_body = []
  pages = OrderedDict()

  # Start from the last paragraph to the first
  paragraphs.reverse()

  regex_digit = re.compile(r'\d+')
  split_text = ''

  for p in paragraphs:

    # Clear the paragraph
    p = clear_data(p)

    if split_text:
      page_body.append(split_text)
      split_text = ''

    # Always add the paragraph (but remove page notation if is there)
    page_body.append(re.sub(page_start_regex, '', p))

    # Save page if there's the page name
    if re.search(page_start_regex, p, flags=re.MULTILINE):

      split_p = re.split(page_start_regex, p)
      if len(split_p) > 1 and split_p[0] and split_p[1]:
        split_text = split_p[0]
        page_body.append(split_p[1])

      # Transform page id in page index: from [019] to 19.
      page_index = re.sub(const.regex_brackets, '',
                          re.findall(page_start_regex, p)[0].strip())

      # Set the index as int
      page_index = regex_digit.findall(page_index)[0]
      page_index = int(page_index.strip())

      # Reverse again the body
      page_body.reverse()

      pages[page_index] = {
          const.key_text: '\n'.join([body.strip() for body in page_body]),
          const.key_paragraphs: [p.strip() for p in page_body]
      }

      pages[page_index][const.key_paragraphs] = list(filter(None, pages[page_index][const.key_paragraphs]))
      page_body = []

  if l != -1:
    pages = OrderedDict(reversed(list(pages.items())))
    while len(pages) > l:
      pages.popitem()

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
            const.footnote_index: current_page[const.key_paragraphs].index(p)+1,
            const.footnote_start: p.index(entity_value),
            const.footnote_end: p.index(entity_value) + len(entity_value)
          })
  
  return None

  
def parse_note_1891(index, row, pages):
  
  entity_page = int(row[const.diaries['1891'][const.key_footnote_header_page]])
  entity_paragraph = int(row[const.diaries['1891'][const.key_footnote_header_paragraph]])
  entity_start = int(row[const.diaries['1891'][const.key_footnote_header_start]])
  entity_end = int(row[const.diaries['1891'][const.key_footnote_header_end]])
  
  entity_value = row[const.diaries['1891'][const.key_footnote_header_value]]
  entity_type = row[const.diaries['1891'][const.key_footnote_header_type]]
  entity_wikidata = row[const.diaries['1891'][const.key_footnote_header_permalinks]]
  entity_annotator = row[const.diaries['1891'][const.key_footnote_header_annotator]]

  permalinks = [f'https://www.wikidata.org/wiki/{entity_wikidata}'] if entity_wikidata else []

    
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
          const.footnote_index: current_page[const.key_paragraphs].index(p)+1,
          const.footnote_start: p.index(entity_value),
          const.footnote_end: p.index(entity_value) + len(entity_value)
        })

  return None


def parse_notes(pages, diary_notes, diary, limit=-1):


  df_diary_notes = pd.read_csv(diary_notes)
  
  df_diary_notes.sort_values(by=const.diaries[diary][const.key_footnote_header_page],ascending=True, inplace=True)
  df_diary_notes.reset_index(drop=True, inplace=True)
  df_diary_notes.fillna('', inplace=True)

  print(df_diary_notes.head())
  
  parsed_notes = {}
  
  for index, row in df_diary_notes.iterrows():

    if index != -1 and index >= limit:
      break

    if diary == '1903':
      note_parsed = parse_note_1903(row, pages)

    if diary == '1891':
      note_parsed = parse_note_1891(index, row, pages)
      
    try:
      note_parsed_id = note_parsed[0]
      note_parsed_body = note_parsed[1]
      parsed_notes[note_parsed_id] = note_parsed_body
      
    except Exception as e:
      print(e)
      continue
            
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

def normalize_Type(t):
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
            const.footnote_fulltext : ent.text,
            const.footnote_index: ps.index(p)+1,
            const.footnote_start: ent.start_char,
            const.footnote_end: ent.end_char,
            const.footnote_type: normalize_Type(ent.label_),
            const.footnote_permalinks: []
          }

          i+=1

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


def parse_metadata():
  df = pd.read_csv(file_metadata)

  # Update the days
  update_days(df)

  # Create metadata.csv file with parsed days
  parse_days(df)

  # Create people_extracted.csv
  parse_people(df)


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
def exec(diaries, exec_upload, config):
  cur_path = os.path.dirname(os.path.realpath(__file__))

  for diary in diaries:
    print(f'### Executing year {diary} ###')

    # Update default paths with specific
    input_path = os.path.join(cur_path, 'assets', 'input')
    output_path = os.path.join(cur_path, 'assets', 'output', diary)
    diary_notes = os.path.join(input_path, const.key_notes_dir, f'{diary}.csv')

    # Check if output_path exists
    writer.create_dir(output_path)

    # Get text and footnote from a docx document
    vec = convert2vec(os.path.join(input_path, f'{diary}.docx'))

    # Parse and write page
    pages = parse_pages(vec[const.key_document], diary)
    writer.write_pages(output_path, pages)
    writer.write_pages_html(output_path, pages, diary)

    # Add Locations found in pages only for 1891
    if diary == '1891':
      input_locations = os.path.join(input_path, 'notes', '1891_Locations.csv')

      # Store WKT value
      for i, row in pd.read_csv(input_locations).iterrows():
        page = row[const.diaries[diary][const.key_footnote_header_page]]

        location_wkt = row[const.diaries[diary][const.key_footnote_header_location_wkt]]
        location_name = row[const.diaries[diary][const.key_footnote_header_location_name]]
        location_link = f'https://www.wikidata.org/wiki/{row[const.diaries[diary][const.key_footnote_header_location_link]]}'
        
        # If there is no wkt, break
        if location_wkt is None:
          break
          
        # Append wkt value
        pages[page][const.key_footnote_header_location_wkt] = location_wkt
        pages[page][const.key_footnote_header_location_name] = location_name 
        pages[page][const.key_footnote_header_location_link] = location_link
  
    # Create RDF Graphs for the diary
    diary_graphs = rdf.diary2graphs(diary)
    rdf.write_graphs(output_path, diary_graphs, 'diary')

    # Create RDF Graphs for the pages
    pages_graphs = rdf.pages2graphs(diary, pages)
    rdf.write_graphs(output_path, pages_graphs, 'document')

    """
    notes_parsed = execute_ner(pages, diary)
    print(notes_parsed)

    df = pd.DataFrame.from_dict(notes_parsed, orient='index')
    df.to_csv(os.path.join(output_path, 'ner.csv'), index=False)
    """
    
    # If there is a note file, parse them as well
    if os.path.exists(diary_notes):
      notes_parsed = parse_notes(pages, diary_notes, diary, limit=20)

    # Run NER to create annotations
    else:
      notes_parsed = execute_ner(pages, diary)

    notes = rdf.footnotes2graphs(diary, notes_parsed)
    rdf.write_graphs(output_path, notes, 'annotation')

  # Upload RDF graphs
  if exec_upload:
    upload.upload(output_path, diary, config)


if __name__ == '__main__':
  exec()
