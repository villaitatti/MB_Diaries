
import sys
import os
import re  
import spacy

sys.path.append('assets')
from convert import convert2text, convert2xml, convert2vec

nlp = spacy.load('en_core_web_sm')

def write_txt(filename, body):
  with open(filename, 'w') as f:
          f.write(body)
          f.close()

def write_ner(filename, body):
  return

def parse_pages(pages):
  regexp = r'\[[0-9]+\][\s]*'
  body = ''
  name = None

  for i, page in enumerate(pages):
    match = re.match(regexp, page)
    if match:
      if name is not None:
        write_txt(os.path.join(output_path, 'txt', name), body)
        write_ner(execute_ner(body))

      name = re.sub(r'[\[\]\s]', '', f'{match[0]}.txt')
      body = f'{re.sub(regexp, "", page)}\n'

    else:
      body += f'{page}\n'
    
def execute_ner(document):



  def show_ents(doc):
    if doc.ents:
      for ent in doc.ents:
        print(f'{ent.text} - {ent.start_char} - {ent.end_char} - {ent.label_} - {spacy.explain(ent.label_)}')

  doc1 = nlp('Iris, Mr. and Mrs.  Curtis of Boston and Cecil lunched here. Miss Stanton and Count and Countess Rasponi came to tea. Miss Lowenthal, professor of Economics at Smith College came to spend the week on.')
  show_ents(doc1)

filename = '1930 DONE Mary Berenson DIary 1930-1931 (People coming to I Tatti).docx'
input_path = os.path.join(os.getcwd(), 'assets', 'input')
output_path = os.path.join(os.getcwd(), 'assets', 'output')
file_input = os.path.join(input_path, filename)

vec = convert2vec(file_input)
parse_pages(vec)

