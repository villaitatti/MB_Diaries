
from spacy.lang.en import English
from asyncore import write
import sys
import os
import re
import spacy
import pandas as pd
import click

# Import the local scripts
sys.path.append('./assets/scripts')
import writer
import upload
import const
import rdf
from convert import convert2text, convert2xml, convert2vec


nlp = spacy.load('en_core_web_trf')


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
  pages = {}

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

      pages[page_index] = {
          const.key_text: '\n'.join([body.strip() for body in page_body]),
          const.key_paragraphs: [p.strip() for p in page_body]
      }

      page_body = []

  return pages


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
      index = [idx for idx, s in enumerate(paragraphs) if footnote_id_complete in s][0]
      match = re.search(text.lower(), paragraphs[index].lower())

      elements[footnote_id] = {
        const.key_footnote_header_page: page_number,
        const.footnote_index: index,
        const.footnote_start: match.start(),
        const.footnote_end: match.end(),
        const.footnote_fulltext: paragraphs[index][match.start():match.end()],
        const.footnote_type: row[const.key_footnote_header_type],
        const.footnote_permalinks: row[const.key_footnote_header_permalinks].split(', ')
      }

      
    except Exception as ex:
      print(f'Error with {footnote_id}: {ex}')
      continue

    # Remove footnote to handle subsequent offsets
    finally:
      re.sub(footnote_id_complete,'',paragraphs[index])
      
  return elements

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

    # Check if output_path exists
    writer.create_dir(output_path)

    # Get text and footnote from a docx document
    vec = convert2vec(os.path.join(input_path, f'{diary}.docx'))

    # Parse and write page
    pages = parse_pages(vec[const.key_document], diary)
    writer.write_pages(output_path, pages)
    writer.write_pages_html(output_path, pages, diary)

    try:
      # If footnotes_cleaned.tsv exist parse them
      df_footnotes_cleaned = pd.read_csv(os.path.join(output_path, 'footnotes_cleaned.tsv'), sep='\t', dtype={const.key_footnote_header_page: str})
      df_footnotes_cleaned = df_footnotes_cleaned.dropna()
      df_footnotes_cleaned = df_footnotes_cleaned.set_index(const.key_footnote_header_id)

      footnotes = parse_footnotes_cleaned(pages, df_footnotes_cleaned)
      graphs = rdf.footnotes2graphs(diary, footnotes)

      rdf.write_graphs(output_path, graphs)
      if exec_upload:
        upload.upload(output_path, diary, config, 'annotation')
      
    except FileNotFoundError:
      footnotes = parse_footnotes(pages, clean_footnotes(vec[const.key_footnote]))
      writer.write_footnotes(output_path, footnotes)
      continue

    """
    # TODO: divide folder based on type eg: footnote, pages etc
    # Create RDF Graphs for the pages
    graphs = rdf.pages2graphs(diary, pages)
    rdf.write_graphs(output_path, graphs)

    # Upload RDF graphs
    if exec_upload:
      upload.upload(output_path, diary, config)
    """
    

if __name__ == '__main__':
  exec()
    
  
