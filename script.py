
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
from dateutil.parser import parse

sys.path.append('./assets')
from convert import convert2text, convert2xml, convert2vec


day_regex = r'(January?|February?|March?|April?|May?|June?|July?|August?|September?|October?|November?|December?)\s*\d*\S*\s*[0-9]{1,2}\s*\S+\s*[0-9]{4}\s*'

endpoint = 'https://collection.itatti.harvard.edu/'

nlp = spacy.load('en_core_web_trf')

tmp1 = 'admin'
tmp2 = 'vitadmin'

key_id = "id"
key_index = "index"
key_page_regex = "page_regex"
key_offset = "offset"

key_body = 'body'
key_text = 'text'

diary_data = {
  "1915": {
    key_id: 491567726,
    key_page_regex: r'\[[0-9]+\][\s]*'
  },
  "1926": {
    key_id: 491567726,
    key_page_regex: r'\[[0-9]+\][\s]*'
  },
  "1927": {
    key_id: 491567726,
    key_page_regex: r'^[\s]*\[[0-9]+\][\s]*$'
  },
  "1930": {
    key_id: 491567726,
    key_page_regex: r'\[[0-9]+\][\s]*'
  },
  "1934": {
    key_id: 491567726,
    key_page_regex: r'\[[0-9]+\][\s]*'
  },
  "1935": {
    key_id: 491567726,
    key_page_regex: r'\[[0-9]+\][\s]*'
  },
}
IIIF_server = 'https://ids.lib.harvard.edu/ids/iiif/'
IIIF_trailer = '/full/full/0/default.jpg'

# Write graphs
def write_day_graph(filename, diary, day):

  create_dir(os.path.dirname(os.path.abspath(filename)))
  g = create_day_graph(diary, day)
  g.serialize(destination=filename, format='turtle')

def write_page_graph(filename, diary, day):
  
  create_dir(os.path.dirname(os.path.abspath(filename)))
  g = create_page_graph(diary, day)
  g.serialize(destination=filename, format='turtle')

def write_diary_graph(filename, diary):

  create_dir(os.path.dirname(os.path.abspath(filename)))
  g = create_diary_graph(diary)
  g.serialize(destination=filename, format='turtle')

# Create graphs
def create_day_graph(diary_number, day):

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

  day_date = day['date']
  page_number = day['page']
  day_index = day['day']
  day_number = int(day_index) + int(page_number) -1

  # Day
  DAY_NODE = URIRef(f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}/day/{day_index}')
  g.add( (DAY_NODE, RDF.type, CRM['E22_Man-Made_Object']) )
  g.add( (DAY_NODE, CRM.P2_has_type, URIRef('https://mbdiaries.itatti.harvard.edu/ontology/Day')) )
  g.add( (DAY_NODE, RDFS.label, Literal(f'Day #{day_index} ({day_date})', datatype=XSD.string)) )
  g.add( (DAY_NODE, CRM.P46i_forms_part_of, URIRef(f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}')))
  g.add( (DAY_NODE, URIRef('https://mbdiaries.itatti.harvard.edu/ontology/order'), Literal(day_index, datatype=XSD.integer)) )

  # Page
  PAGE_NODE = URIRef(f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}/page/{page_number}')
  g.add( (DAY_NODE, CRM.P62i_is_depicted_by, PAGE_NODE) )

  g.namespace_manager.bind('Platform', PLATFORM, override=True, replace=True)
  g.namespace_manager.bind('crm', CRM, override=True, replace=True)
  g.namespace_manager.bind('crmdig', CRMDIG, override=True, replace=True)
  g.namespace_manager.bind('ldp', LDP, override=True, replace=True)
  g.namespace_manager.bind('prov', PROV, override=True, replace=True)

  return g

def create_page_graph(diary_number, day):

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

  page_number = day['page']
  day_index = day['day']
  day_number = page_number

  # Page
  PAGE_NODE = URIRef(f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}/page/{page_number}')

  # Page File
  PAGE_NODE_DOCUMENT = URIRef(f'https://mbdiaries.itatti.harvard.edu/document/{diary_number}/page/{page_number}')
  g.add( (PLATFORM.fileContainer, LDP.contains, PAGE_NODE_DOCUMENT) )
  g.add( (PAGE_NODE_DOCUMENT, RDF.type, PLATFORM.File) )
  g.add( (PAGE_NODE_DOCUMENT, RDF.type, LDP.Resource) )
  g.add( (PAGE_NODE_DOCUMENT, RDF.type, URIRef('https://mbdiaries.itatti.harvard.edu/ontology/Document')) )
  g.add( (PAGE_NODE_DOCUMENT, RDFS.label, Literal(f'Document file of {page_number}.html', datatype=XSD.string)) )
  g.add( (PAGE_NODE_DOCUMENT, PLATFORM.fileContext, URIRef('http://www.researchspace.org/resource/TextDocuments')) )
  g.add( (PAGE_NODE_DOCUMENT, PLATFORM.fileName, Literal(f'{page_number}.html', datatype=XSD.string)) )
  g.add( (PAGE_NODE_DOCUMENT, PLATFORM.mediaType, Literal('form-data', datatype=XSD.string)) )
  g.add( (PAGE_NODE_DOCUMENT, PROV.wasAttributedTo, Literal(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), datatype=XSD.dateTime)) )
  g.add( (PAGE_NODE_DOCUMENT, PROV.generatedAtTime, URIRef('http://www.researchspace.org/resource/admin')) )
  g.add( (PAGE_NODE, CRM.P129i_is_subject_of, PAGE_NODE_DOCUMENT) ) 

  # Visual representation
  IMAGE_NODE = URIRef(f'{IIIF_server}{int(diary_data[diary_number][key_id])+int(day_number)}{IIIF_trailer}')
  g.add( (IMAGE_NODE, RDF.type, CRM.E38_Image) )
  g.add( (IMAGE_NODE, RDF.type, URIRef('http://www.researchspace.org/ontology/EX_Digital_Image')) )
  g.add( (PAGE_NODE, CRM.P183i_has_representation, IMAGE_NODE) )

  g.namespace_manager.bind('Platform', PLATFORM, override=True, replace=True)
  g.namespace_manager.bind('crm', CRM, override=True, replace=True)
  g.namespace_manager.bind('crmdig', CRMDIG, override=True, replace=True)
  g.namespace_manager.bind('ldp', LDP, override=True, replace=True)
  g.namespace_manager.bind('prov', PROV, override=True, replace=True)

  return g

def create_diary_graph(diary_number):

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

  diary_uri = f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}'

  # Diary
  BASE_NODE = URIRef(diary_uri)
  g.add( (PLATFORM.fileContainer, LDP.contains, BASE_NODE) )
  g.add( (BASE_NODE, RDF.type, CRM['E22_Man-Made-Object']) )
  g.add( (BASE_NODE, CRM.P2_has_type, URIRef('https://mbdiaries.itatti.harvard.edu/ontology/Diary')) )
  g.add( (BASE_NODE, RDFS.label, Literal(diary_number, datatype=XSD.string)) )

  # Visual representation
  IMAGE_NODE = URIRef(f'{IIIF_server}{int(diary_data[diary_number][key_id]+1)}{IIIF_trailer}')
  g.add( (BASE_NODE, CRM.P183i_has_representation, IMAGE_NODE) )
  g.add( (IMAGE_NODE, RDF.type, CRM.E38_Image) )
  g.add( (IMAGE_NODE, RDF.type, URIRef('http://www.researchspace.org/ontology/EX_Digital_Image')) )

  g.namespace_manager.bind('Platform', PLATFORM, override=True, replace=True)
  g.namespace_manager.bind('crm', CRM, override=True, replace=True)
  g.namespace_manager.bind('crmdig', CRMDIG, override=True, replace=True)
  g.namespace_manager.bind('ldp', LDP, override=True, replace=True)
  g.namespace_manager.bind('prov', PROV, override=True, replace=True)

  return g

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

def write_pages(output_path, pages):
  
  for page in pages:
    
    if key_text in page:
      write_file(os.path.join(output_path, 'txt', f'day_{page[key_index]}.txt'), page[key_text])

  return pages

def parse_pages(paragraphs, diary, stop=None):

  page_start_regex = diary_data[diary][key_page_regex]

  day_index = 0
  day_body = []

  days = []

  # Start from the last paragraph to the first
  paragraphs.reverse()
  for p in paragraphs:

    # Prevent page annotation
    if not re.match(page_start_regex, p):

      # Update page body
      day_body.append(p)

      if re.search(day_regex, p):

        day_body.reverse()

        days.append({
          key_index: day_index,
          key_text: '\n'.join(day_body)
        })

        day_index += 1
        day_body = []

  for day in days:
    day[key_index] = abs(len(days) - day[key_index])

  return days
 
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

# Upload metadata
def _del(filename, url):

  # curl -v -u admin:admin -X DELETE -H 'Content-Type: text/turtle' http://127.0.0.1:10214/rdf-graph-store?graph=http%3A%2F%2Fdpub.cordh.net%2Fdocument%2FBernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html%2Fcontext

  command = f'curl -u {tmp1}:{tmp2} -X DELETE -H \'Content-Type: text/turtle\' {url}'

  return f'DEL\t{os.system(command)}'

def _post(filename, url):

    #curl -v -u admin:admin -X POST -H 'Content-Type: text/turtle' --data-binary '@metadata/Bernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html.ttl' http://127.0.0.1:10214/rdf-graph-store?graph=http%3A%2F%2Fdpub.cordh.net%2Fdocument%2FBernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html%2Fcontext

    command = f'curl -u {tmp1}:{tmp2} -X POST -H \'Content-Type: text/turtle\' --data-binary \'@{filename}\' {url}'

    return f'POST\t{os.system(command)}'

def upload(output_path, diary, dir, type):

  diary_dir = os.path.join(output_path, 'ttl', dir)

  for i, ttl_file in enumerate(os.listdir(diary_dir)):

    file_name = ttl_file.replace('.ttl', '')

    graph_name = f'https://mbdiaries.itatti.harvard.edu/{type}/{diary}/{dir}/{file_name}/context'

    print(f'\n{graph_name}')
    graph_name = urllib.parse.quote(graph_name)

    r_url = f'{endpoint}rdf-graph-store/?graph={graph_name}'
    
    # DEL
    print(_del(ttl_file, r_url))

    # PUT
    print(_post(os.path.join(diary_dir, ttl_file), r_url))

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
      write_xlsx(os.path.join(xlsx_path,f'{name_file}.xlsx'), ner_body_curr)

# Default paths
cur_path = os.path.dirname(os.path.realpath(__file__))

filenames = ['1927']
stop = None

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
  pages = parse_pages(vec, filename, stop)
  pages = write_pages(output_path, pages)

  # Upload
  #upload(output_path, filename, 'day', 'diary')
  #upload(output_path, filename, 'page', 'document')
