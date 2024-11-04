import zipfile
from docx import Document
from xml.etree.ElementTree import XML
import const

WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
PARA = WORD_NAMESPACE + 'p'
TEXT = WORD_NAMESPACE + 't'
COMMENT = WORD_NAMESPACE + 'comment'
TABLE = WORD_NAMESPACE + 'tbl'
ROW = WORD_NAMESPACE + 'tr'
CELL = WORD_NAMESPACE + 'tc'


def convert2xml(path):
  p = _parsedocx(path)
  for index, para in enumerate(p):
    p[index] = f'<p>{para}</p>'
  return '\n'.join(p)


"""
def convert2vec(path):
  return _parsedocx(path)
"""


def convert2vec(path):
  parsed_doc = extract_paragraphs(path)

  return {
    const.key_document: parsed_doc,
    # const.key_footnote: parsed_doc.footnotes[0][0]
  }


def convert_text2vec(path):
  with open(path, "r") as myfile:
    d = myfile.readlines()
  return {
      const .key_document: d
  }


def convert2text(path):
  p = _parsedocx(path)
  return '\n'.join(p)


def extract_paragraphs(docx_path):
  """
  Extracts paragraphs from a docx document, excluding footnotes and other non-main text elements.

  Parameters:
  docx_path (str): Path to the .docx file to be processed.

  Returns:
  list of str: A list containing the text of each extracted paragraph.
  """
  document = Document(docx_path)
  paragraphs = []

  # Bold text is indicated a day
  for para in document.paragraphs:

    if para.text:
      if para.runs:
        if para.runs[0].bold:
          paragraphs.append(f'{const.key_note_header}{para.text}')
        else:
          paragraphs.append(para.text)

  return paragraphs


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
