import html
import os
import pandas as pd
import re
import json
from . import const


def create_dir(dir_path):
  if not os.path.exists(dir_path):
    os.makedirs(dir_path)


def write_file(filename, body):

  create_dir(os.path.dirname(os.path.abspath(filename)))
  with open(filename, 'w', encoding='utf-8') as f:
    f.write(body)


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
  df_footnotes = pd.DataFrame(footnotes, columns=const.header_footnotes)

  df_footnotes.to_excel(os.path.join(output_path, "footnotes.xlsx"))
  df_footnotes.to_csv(os.path.join(output_path, "footnotes.csv"))


def write_pages(output_path, pages):

  for key, page in pages.items():

    if const.key_text in page:
      write_file(os.path.join(output_path, 'txt',
                 f'{key}.txt'), page[const.key_text])

  return pages


_TAG_BY_TYPE = {
    const.KEY_BOLD: 'b',
    const.KEY_ITALIC: 'i',
    const.KEY_UNDERLINE: 'u',
    const.KEY_STRIKE: 's',
}


def _merge_whitespace_between_same_tags(runs):
  # A plain whitespace-only run sandwiched between two runs of the same
  # formatting type (e.g. <u>Hamel</u> <u>Jacques,</u>) would otherwise
  # render with an unstyled gap between the tags. Absorb the whitespace into
  # the surrounding tag instead, so the run of formatting stays continuous.
  runs = [dict(run) for run in runs]
  changed = True
  while changed:
    changed = False
    for i in range(len(runs) - 2):
      before, gap, after = runs[i], runs[i + 1], runs[i + 2]
      if (before[const.KEY_TYPE] == after[const.KEY_TYPE]
              and before[const.KEY_TYPE]
              and not gap[const.KEY_TYPE]
              and gap[const.KEY_VALUE].strip() == ''):
        merged_run = {
            const.KEY_VALUE: before[const.KEY_VALUE] + gap[const.KEY_VALUE] + after[const.KEY_VALUE],
            const.KEY_TYPE: before[const.KEY_TYPE],
        }
        runs = runs[:i] + [merged_run] + runs[i + 3:]
        changed = True
        break
  return runs


def write_pages_html(output_path, pages, diary, app_path=None):

  for key, page in pages.items():
    if const.key_paragraphs in page:

      body = ''
      for line in page[const.key_paragraphs]:
        run_fragments = []
        for run in _merge_whitespace_between_same_tags(line[const.KEY_RUNS]):
          # quote=False: only escape &, <, > -- the text-node-safe subset.
          # Quotes are legal (and common) in running prose and don't need
          # &quot;/&#x27; here.
          value = html.escape(run[const.KEY_VALUE], quote=False)
          for flag in run[const.KEY_TYPE]:
            tag = _TAG_BY_TYPE[flag]
            value = f'<{tag}>{value}</{tag}>'
          run_fragments.append(value)

        body += '\n\t\t<p>' + ''.join(run_fragments).strip() + '</p>'

      page_html = f'<html>\n\t<body>{body}\n\t</body>\n</html>'

      write_file(os.path.join(output_path, 'html',
                 f'{diary}_{key}.html'), page_html)

      if app_path:
        file_path = os.path.join(app_path, 'file', f'{diary}_{key}.html')
        try:
          if os.path.exists(file_path):
            os.remove(os.path.join(file_path))
          write_file(file_path, page_html)
        except Exception as e:
          print(e)
