import zipfile
from xml.etree.ElementTree import XML

WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
PARA = WORD_NAMESPACE + 'p'
TEXT = WORD_NAMESPACE + 't'
TABLE = WORD_NAMESPACE + 'tbl'
ROW = WORD_NAMESPACE + 'tr'
CELL = WORD_NAMESPACE + 'tc'

def parsedocx(path):
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
