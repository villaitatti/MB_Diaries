
import sys
import os
import re
import spacy
import pandas as pd
import numpy as np
import datetime

sys.path.append('./assets')
from convert import convert2text, convert2xml, convert2vec

nlp = spacy.load('en_core_web_trf')

def write_file(filename, body):

  create_dir(os.path.dirname(os.path.abspath(filename)))
  with open(filename, 'w') as f:
    f.write(body)
    f.close()

def write_csv(filename, body):
  create_dir(os.path.dirname(os.path.abspath(filename))) 
  df = pd.DataFrame(
      body, columns=['page', 'text', 'p', 'start', 'end', 'type', 'description'])
  df.to_csv(filename, index=False)

def parse_pages(pages):
  regexp = r'\[[0-9]+\][\s]*'
  body = ''
  body_html = ''
  name = None

  ner_body = []
  for i, page in enumerate(pages):
    match = re.match(regexp, page)
    if match:
      if name is not None:
        print(f'\t\tParsing page {name}')

        write_file(os.path.join(output_path, 'txt', f'{name}.txt'), body)

        body_html = f'<!DOCTYPE html>\n<html>\n\t<head>\n\t\t<title>{name}</title>\n\t</head>\n\t<body>\n{body_html}</body></html>'
        write_file(os.path.join(output_path, 'html', f'{name}.html'), body_html)

        body_html = ''

        ner_body_curr = execute_ner(body, name)
        ner_body.extend(ner_body_curr)

        write_csv(os.path.join(output_path, 'csv',
                  f'{name}.csv'), ner_body_curr)

      name = re.sub(r'[\[\]\s]', '', match[0])
      body = f'{re.sub(regexp, "", page)}\n'

    else:
      body += f'{page}\n'
      body_html += f'\t\t<p>{page}</p>\n'

  write_csv(os.path.join(output_path, 'csv',
                         f'total.csv'), ner_body)

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
  df_out['image_link'] = 'https://iiif.lib.harvard.edu/manifests/view/drs:493343177$' + df_out["page"].astype(str) + 'i'
  df_out = df_out.rename(columns={'text': 'day_title'})

  df_out.to_csv(os.path.join(output_path, 'csv', 'metadata.csv'), columns=['day', 'day_title', 'page', 'image_link'], index=False)

def parse_people(df):

  print(df.head())
  people = df['type'].str.fullmatch('PERSON')

  df_out = df[people].copy()
  df_out.to_csv(os.path.join(output_path, 'csv', 'people_extracted.csv'), columns=['day', 'text', 'description', 'page', 'p', 'start', 'end'], index=False)

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

def create_dir(dir_path):
  if not os.path.exists(dir_path):
    os.makedirs(dir_path)


# Default paths
cur_path = os.path.dirname(os.path.realpath(__file__))

filenames = ['1916']

for filename in filenames:

  print(f'### Executing year {filename} ###')

  # Update default paths with specific 
  input_path = os.path.join(cur_path, 'assets', 'input')
  output_path = os.path.join(cur_path, 'assets', 'output', filename)

  # Check if output_path exists
  create_dir(output_path)

  file_input = os.path.join(input_path, f'{filename}.docx')

  vec = convert2vec(file_input)

  # Execute page
  parse_pages(vec)

  # Execute NER
  """
  file_metadata = os.path.join(output_path, 'csv', filename, 'total.csv')
  parse_metadata()
  """

  print()
    
