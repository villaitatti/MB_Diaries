
from asyncore import write
import sys
import os
import re
from xml.dom import NamespaceErr
import spacy
import pandas as pd
import numpy as np
import datetime
import urllib
from rdflib import Graph, URIRef, namespace, Namespace, Literal

sys.path.append('./assets')
from convert import convert2text, convert2xml, convert2vec

endpoint = 'http://localhost:10214/'

tmp1 = 'admin'
tmp2 = 'admin'

def create_graph(diary_number, page_number):

  g = Graph()

  # Namespaces
  PLATFORM = Namespace('http://www.researchspace.org/resource/system/')
  LDP = Namespace('http://www.w3.org/ns/ldp#')
  CRM = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
  DPUB_ANNOTATION = Namespace('https://mbdiaries.itatti.harvard.edu/document/annotation-schema/')
  CRMDIG = Namespace('http://www.ics.forth.gr/isl/CRMdig/')
  PROV = Namespace('http://www.w3.org/ns/prov#')
  RDF = namespace.RDF
  RDFS = namespace.RDFS
  XSD = namespace.XSD

  # Base node
  BASE_NODE = URIRef(f'https://mbdiaries.itatti.harvard.edu/document/{diary_number}/{page_number}')

  # LDP file container
  g.add( (PLATFORM.fileContainer, LDP.contains, BASE_NODE) )

  g.add( (BASE_NODE, RDF.type, PLATFORM.File) )
  g.add( (BASE_NODE, RDF.type, URIRef('https://mbdiaries.itatti.harvard.edu/ontology/Document')) )

  g.add( (BASE_NODE, RDFS.label, Literal(page_number, datatype=XSD.string)) )
  g.add( (BASE_NODE, PLATFORM.fileContext, URIRef('http://www.researchspace.org/resource/TextDocuments')) )
  g.add( (BASE_NODE, PLATFORM.fileName, Literal(f'{page_number}.html', datatype=XSD.string)) )
  g.add( (BASE_NODE, PLATFORM.mediaType, Literal('form-data', datatype=XSD.string)) )
  g.add( (BASE_NODE, PROV.wasAttributedTo, Literal(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), datatype=XSD.dateTime)) )
  g.add( (BASE_NODE, PROV.generatedAtTime, URIRef('http://www.researchspace.org/resource/admin')) )

  g.namespace_manager.bind('Platform', PLATFORM, override=True, replace=True)
  g.namespace_manager.bind('crm', CRM, override=True, replace=True)
  g.namespace_manager.bind('crmdig', CRMDIG, override=True, replace=True)
  g.namespace_manager.bind('ldp', LDP, override=True, replace=True)
  g.namespace_manager.bind('prov', PROV, override=True, replace=True)

  return g

def write_graph(filename, diary, name):

  create_dir(os.path.dirname(os.path.abspath(filename)))
  g = create_graph(diary, name)
  g.serialize(destination=filename, format='turtle')

def write_file(filename, body):

  create_dir(os.path.dirname(os.path.abspath(filename)))
  with open(filename, 'w') as f:
    f.write(body)
    f.close()

def write_csv(filename, body):
  create_dir(os.path.dirname(os.path.abspath(filename))) 
  df = pd.DataFrame(
      body, columns=['page', 'text', 'p', 'start', 'end', 'type', 'description'])

  df['wikidata'] = ''
  df['viaf'] = ''
  df['loc'] = ''
  df['notes'] = ''

  df.to_csv(filename, index=False)

def write_xlsx(filename, body):
  create_dir(os.path.dirname(os.path.abspath(filename))) 
  df = pd.DataFrame(
      body, columns=['page', 'text', 'p', 'start', 'end', 'type', 'description'])

  df['wikidata'] = ''
  df['viaf'] = ''
  df['loc'] = ''
  df['notes'] = ''

  df.to_excel(filename, index=False)

def parse_pages(output_path ,pages, diary):

  regexp = r'\[[0-9]+\][\s]*'
  body = ''
  body_html = ''
  name = None

  for page in pages:
    match = re.match(regexp, page)

    # if it's a paragraph containing a page heading 
    # eg: "Friday, January 1, 1915, I Tatti"
    if match:
      if name is not None:
        print(f'Parsing page {name}')

        # Text file
        write_file(os.path.join(output_path, 'txt', f'{name}.txt'), body)

        # HTML file
        body_html = f'<!DOCTYPE html>\n<html>\n\t<head>\n\t\t<title>{name}</title>\n\t</head>\n\t<body>\n{body_html}</body></html>'
        write_file(os.path.join(output_path, 'html', f'{name}.html'), body_html)

        # Turtle file
        write_graph(os.path.join(output_path, 'ttl', f'{name}.ttl'), diary, name)

        body_html = ''

      name = re.sub(r'[\[\]\s]', '', match[0])
      body = f'{re.sub(regexp, "", page)}\n'

    # internal paragraphs
    else:
      body += f'{page}\n'
      body_html += f'\t\t<p>{page}</p>\n'

def execute_ner(nlp, document, name):

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

# Upload metadata
def _del(filename, url):

  # curl -v -u admin:admin -X DELETE -H 'Content-Type: text/turtle' http://127.0.0.1:10214/rdf-graph-store?graph=http%3A%2F%2Fdpub.cordh.net%2Fdocument%2FBernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html%2Fcontext

  command = f'curl -u {tmp1}:{tmp2} -X DELETE -H \'Content-Type: text/turtle\' {url}'

  return f'DEL\t{os.system(command)}'

def _post(filename, url):

    #curl -v -u admin:admin -X POST -H 'Content-Type: text/turtle' --data-binary '@metadata/Bernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html.ttl' http://127.0.0.1:10214/rdf-graph-store?graph=http%3A%2F%2Fdpub.cordh.net%2Fdocument%2FBernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html%2Fcontext

    command = f'curl -u {tmp1}:{tmp2} -X POST -H \'Content-Type: text/turtle\' --data-binary \'@{filename}\' {url}'

    return f'POST\t{os.system(command)}'

def upload(diary_dir, diary):

  for i, ttl_file in enumerate(os.listdir(diary_dir)):

    if i > 10:
      break

    file_name = ttl_file.replace('.ttl', '')
    graph_name = urllib.parse.quote(f'https://mbdiaries.itatti.harvard.edu/document/{diary}/{file_name}/context')

    r_url = f'{endpoint}?graph={graph_name}'

    print(f'\n{filename}')

    # DEL
    print(_del(ttl_file, r_url))

    # PUT
    print(_post(ttl_file, r_url))

def ner(output_path):
  nlp = spacy.load('en_core_web_trf')
  txt_path = os.path.join(output_path, 'txt')
  csv_path = os.path.join(output_path, 'csv')
  xlsx_path = os.path.join(output_path, 'xslx')

  ner_body = []

  for txt_file in os.listdir(txt_path):

    name_file = txt_file.replace('.txt', '')
    
    with open(os.path.join(txt_path, txt_file), 'r') as f:

      ner_body_curr = execute_ner(nlp, f.read(), name_file)
      ner_body.append(ner_body_curr)

      write_xlsx(os.path.join(xlsx_path,f'{name_file}.xlsx'), ner_body_curr)

# Default paths
cur_path = os.path.dirname(os.path.realpath(__file__))

filenames = ['1922']

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
  parse_pages(output_path, vec, filename)

  # Execute NER
  ner(output_path)
  
  # Upload
  # upload(os.path.join(output_path, 'ttl'), filename)

  print()
    
