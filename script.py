
import sys
import os
import re
import spacy
import pandas as pd

sys.path.append('/Users/gspinaci/projects/diaries/MB_Diaries/assets')
from convert import convert2text, convert2xml, convert2vec

nlp = spacy.load('en_core_web_trf')


def write_file(filename, body):
  with open(filename, 'w') as f:
    f.write(body)
    f.close()


def write_csv(filename, body):
  df = pd.DataFrame(
      body, columns=['text', 'p', 'start', 'end', 'type', 'description'])
  df.to_csv(filename, index=False)


def parse_pages(pages):
  regexp = r'\[[0-9]+\][\s]*'
  body = ''
  name = None

  for i, page in enumerate(pages):
    match = re.match(regexp, page)
    if match:
      if name is not None:
        write_file(os.path.join(output_path, 'txt', f'{name}.txt'), body)
        write_csv(os.path.join(output_path, 'csv',
                  f'{name}.csv'), execute_ner(body))

      name = re.sub(r'[\[\]\s]', '', match[0])
      body = f'{re.sub(regexp, "", page)}\n'

    else:
      body += f'{page}\n'


def execute_ner(document):
  data = []
  pages = document.split('\n')
  for idx, page in enumerate(pages):
    doc = nlp(page)
    for ent in doc.ents:
      data.append([ent.text, idx+1, ent.start_char, ent.end_char,
                  ent.label_, spacy.explain(ent.label_)])

  return data


filename = '1930 DONE Mary Berenson DIary 1930-1931 (People coming to I Tatti).docx'
cur_path = os.path.dirname(os.path.realpath(__file__))
input_path = os.path.join(cur_path, 'assets', 'input')
output_path = os.path.join(cur_path, 'assets', 'output')
file_input = os.path.join(input_path, filename)

vec = convert2vec(file_input)
parse_pages(vec)
