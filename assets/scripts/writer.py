import os
import utils
import pandas as pd
import re
from const import key_text, key_index, regex_footnote_id

def write_file(filename, body):

  utils.create_dir(os.path.dirname(os.path.abspath(filename)))
  with open(filename, 'w') as f:
    f.write(body)
    f.close()


def write_csv(filename, body):
  utils.create_dir(os.path.dirname(os.path.abspath(filename)))
  df = pd.DataFrame(
      body, columns=['page', 'text', 'p', 'start', 'end', 'type', 'description'])

  df['wikidata'] = ''
  df['viaf'] = ''
  df['loc'] = ''
  df['notes'] = ''

  df.to_csv(filename, index=False)


def write_xlsx(filename, body):
  utils.create_dir(os.path.dirname(os.path.abspath(filename)))
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
      write_file(os.path.join(output_path, 'txt',
                 f'{page[key_index]}.txt'), page[key_text])

  return pages

  
def write_pages_html(output_path, pages):
  for page in pages:

    if key_text in page:

      # Split by \n and add <p>
      lines = page[key_text].split('\n')
      body = ''

      for line in lines:
        line = line.strip()
        if line:
          line = re.sub(regex_footnote_id, '', line)
          body += f'\n\t\t<p>{line}<p>'

      html = f'<html>\n\t<body>{body}\n\t</body>\n</html>'
      
      write_file(os.path.join(output_path, 'html',
                 f'{page[key_index]}.html'), html)
