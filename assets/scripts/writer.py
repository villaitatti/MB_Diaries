import os
import pandas as pd
import re
import json
from const import key_text, key_index, regex_footnote_id, header_footnotes, key_paragraphs, key_type


def create_dir(dir_path):
  if not os.path.exists(dir_path):
    os.makedirs(dir_path)


def write_file(filename, body):

  create_dir(os.path.dirname(os.path.abspath(filename)))
  with open(filename, 'w') as f:
    f.write(body)
    f.close()


def write_csv(filename, body, header):
  create_dir(os.path.dirname(os.path.abspath(filename)))
  df = pd.DataFrame(body, columns=header)
  df.to_csv(filename, index=False)


def write_json(filename, body):
  # write json file with indent 4
  create_dir(os.path.dirname(os.path.abspath(filename)))
  with open(filename, 'w') as f:
    json.dump(body, f, indent=4)
    f.close()


def write_xlsx(filename, body, header):
  create_dir(os.path.dirname(os.path.abspath(filename)))
  df = pd.DataFrame(body, columns=header)
  df.to_excel(filename, index=False)


def write_footnotes(output_path, footnotes):
  df_footnotes = pd.DataFrame(footnotes, columns=header_footnotes)

  df_footnotes.to_excel(os.path.join(output_path, "footnotes.xlsx"))
  df_footnotes.to_csv(os.path.join(output_path, "footnotes.csv"))


def write_pages(output_path, pages):

  for key, page in pages.items():

    if key_text in page:
      write_file(os.path.join(output_path, 'txt',
                 f'{key}.txt'), page[key_text])

  return pages


def write_pages_html(output_path, pages, diary, app_path=None):

  for key, page in pages.items():
    if key_paragraphs in page:

      body = ''
      for line in page[key_paragraphs]:
        body += f'\n\t\t<{line[key_type]
                          }>{line[key_text]}</{line[key_type]}>'

      html = f'<html>\n\t<body>{body}\n\t</body>\n</html>'

      write_file(os.path.join(output_path, 'html',
                 f'{diary}_{key}.html'), html)

      if app_path:
        file_path = os.path.join(app_path, 'file', f'{diary}_{key}.html')
        try:
          if os.path.exists(file_path):
            os.remove(os.path.join(file_path))
          write_file(file_path, html)
        except Exception as e:
          print(e)
