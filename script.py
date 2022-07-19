
from asyncore import write
import sys
import os
import re
from xml.dom import NamespaceErr
import spacy
import pandas as pd
import numpy as np


sys.path.append('./assets/scripts')
from convert import convert2text, convert2xml, convert2vec
import const
import utils
import writer

endpoint = 'https://collection.itatti.harvard.edu/'

nlp = spacy.load('en_core_web_trf')


# Execute parsing data
def do_pages(output_path, vec, diary):

  pages = parse_pages(output_path, vec["document"], diary, stop)
  pages = writer.write_pages(output_path, pages)


def parse_pages(output_path, paragraphs, diary, stop=None):

  def update_page(page_index, page_body):
    # Update body n-1 page
    if page_index > 0:
      pages[page_index-1][const.key_text] = page_body

  page_start_regex = const.diary_data[diary][const.key_page_regex_check]

  page_index = 0
  page_body = ''

  pages = []

  for p in paragraphs:

    p = p.strip()

    # Check if here there's the start of a page
    page_match = re.match(page_start_regex, p)
    if not page_match:
      page_body += f'{p}\n'

    else:

      # Add n page
      pages.append({
          const.key_index: re.sub(r'[\[\]]', '', p)
      })

      update_page(page_index, page_body)

      page_index += 1
      page_match = None
      page_body = ''

  update_page(page_index, page_body)

  return pages


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

      ner_body_curr = execute_ner(nlp, f.read(), name_file)
      ner_body.append(ner_body_curr)

      write_csv(os.path.join(csv_path, f'{name_file}.csv'), ner_body_curr)
      write_xlsx(os.path.join(xlsx_path, f'{name_file}.xlsx'), ner_body_curr)


# Default paths
cur_path = os.path.dirname(os.path.realpath(__file__))

filenames = ['1933']
stop = None

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
