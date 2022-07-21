
from spacy.lang.en import English
from asyncore import write
import sys
import os
import re
from xml.dom import NamespaceErr
import spacy
import pandas as pd
import numpy as np

# Import the local scripts
sys.path.append('./assets/scripts')
import writer
import utils
import const
from convert import convert2text, convert2xml, convert2vec


endpoint = 'https://collection.itatti.harvard.edu/'

nlp = spacy.load('en_core_web_trf')

# Execute parsing data


def do_pages(output_path, vec, diary):

  # Parse and write page
  pages = parse_pages(vec[const.key_document], diary)

  writer.write_pages(output_path, pages)
  writer.write_pages_html(output_path, pages)

  # Clean and parse footnotes
  footnotes = parse_footnotes(pages, clean_footnotes(vec[const.key_footnote]))
  writer.write_footnotes(output_path, footnotes)


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


def parse_pages(paragraphs, diary):

  page_start_regex = const.diary_data[diary][const.key_page_regex_check]
  page_body = []
  pages = []

  # Start from the last paragraph to the first
  paragraphs.reverse()
  for p in paragraphs:

    # Always add the paragraph (but remove page notation if is there)
    page_body.append(re.sub(page_start_regex, '', p))

    # Save page if there's the page name
    if re.match(page_start_regex, p):
      # Transform page id in page index: from [019] to 19.
      page_index = re.sub(const.regex_brackets, '',
                          re.findall(page_start_regex, p)[0].strip())

      page_body.reverse()

      pages.append({
          const.key_index: page_index,
          const.key_text: '\n'.join([body.strip() for body in page_body])
      })

      page_body = []

  return pages


def parse_footnotes(pages, footnotes):

  elements = []

  # Link footnotes
  for page in pages:

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
          element = [page[const.key_index], identifier, tokens[-4:], footnotes[identifier][const.footnote_fulltext],
                     footnotes[identifier][const.footnote_type], ', '.join(footnotes[identifier][const.footnote_permalinks])]
        else:
          element = [page[const.key_index], identifier, tokens[-4:], footnotes[identifier]
                     [const.footnote_fulltext], footnotes[identifier][const.footnote_type], '']

        elements.append(element)

    except Exception as ex:
      print(ex)

  return footnotes


def execute_ner(document, name):

  data = []
  pages = document.split('\n')
  for idx, page in enumerate(pages):
    doc = nlp(page)
    for ent in doc.ents:
      data.append([name, ent.text, idx+1, ent.start_char, ent.end_char,
                  ent.label_, spacy.explain(ent.label_)])

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


# Default paths
cur_path = os.path.dirname(os.path.realpath(__file__))

filenames = ['1933']

for filename in filenames:

  print(f'### Executing year {filename} ###')

  # Update default paths with specific
  input_path = os.path.join(cur_path, 'assets', 'input')
  output_path = os.path.join(cur_path, 'assets', 'output', filename)

  # Check if output_path exists
  utils.create_dir(output_path)

  file_input = os.path.join(input_path, f'{filename}.docx')

  vec = convert2vec(file_input)

  # Execute page
  do_pages(output_path, vec, filename)

  # Upload
  #upload(output_path, filename, 'day', 'diary')
  #upload(output_path, filename, 'page', 'document')
