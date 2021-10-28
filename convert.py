import zipfile
from xml.etree.ElementTree import XML

WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
PARA = WORD_NAMESPACE + 'p'
TEXT = WORD_NAMESPACE + 't'
TABLE = WORD_NAMESPACE + 'tbl'
ROW = WORD_NAMESPACE + 'tr'
CELL = WORD_NAMESPACE + 'tc'

def convert2xml(path):
  p = _parsedocx(path)
  for index, para in enumerate(p):
    p[index] = f'<p>{para}</p>'
  return '\n'.join(p)


def convert2text(path):
  p = _parsedocx(path)
  return '\n'.join(p)

def _parsedocx(path):
  with zipfile.ZipFile(path) as docx:
    tree = XML(docx.read('word/document.xml'))
    paragraphs = []
    for paragraph in tree.iter(PARA):
      texts = [node.text
               for node in paragraph.iter(TEXT)
               if node.text]
      if texts:
        paragraphs.append(''.join(texts))
  return paragraphs
