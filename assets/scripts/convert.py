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

  
def _extract_paragraphs_from_docx(docx_path):
  try:
    doc = Document(docx_path)
    paragraphs = [_extract_paragraph(para)
                  for para in doc.paragraphs if para]
    if len(paragraphs) > 0:
      return [para for para in paragraphs if para is not None]
    return []
  except Exception as e:
    print(str(e))


def _extract_paragraph(para):
  runs = []
  current_position = 0  # To track the position of each run in the paragraph
  for run in para.runs:
    run_text = run.text.strip()
    if run_text:
      # Get the run's information and append it to the runs list
      run_data = _extract_run(run, current_position)
      runs.append(run_data)
      # Update the current position for the next run, adding the length of the text
      current_position += len(run.text)

  if runs:
    return {
        const.KEY_TEXT: para.text.strip(),
        const.KEY_RUNS: runs
    }
  return None


def _extract_run(run, start_position):
  run_text = run.text
  run_type = _get_run_type(run)
  return {
      const.KEY_VALUE: run_text,
      const.KEY_TYPE: run_type,
      const.KEY_START_POSITION: start_position,  # Adding start position to the run data
      const.KEY_END_POSITION: start_position + len(run_text)  # Adding end position to the run data
  }


def _get_run_type(run):
  if run.bold:
    return const.KEY_BOLD
  elif run.italic:
    return const.KEY_ITALIC
  elif run.underline:
    return const.KEY_UNDERLINE
  elif run.font.strike:
    return const.KEY_STRIKE
  return const.KEY_TEXT


def extract_paragraphs(docx_path):
  paragraphs = _extract_paragraphs_from_docx(docx_path)

  return paragraphs


def _parsedocx(path):
    """
    Extracts text and formatting from a .docx file using XML parsing.

    Parameters:
    path (str): Path to the .docx file.

    Returns:
    list of dict: A list containing dictionaries with paragraphs and their styled runs.
    """
    with zipfile.ZipFile(path) as docx:
        # Parse the document.xml file
        tree = XML(docx.read('word/document.xml'))
        paragraphs = []

        for paragraph in tree.iter(f"{{{WORD_NAMESPACE['w']}}}p"):
            # Collect paragraph data
            paragraph_data = {"text": "", "styled_runs": []}
            texts = []

            for run in paragraph.iter(f"{{{WORD_NAMESPACE['w']}}}r"):
                # Get the text content of the run
                text_node = run.find(f"{{{WORD_NAMESPACE['w']}}}t")
                if text_node is not None and text_node.text:
                    text_content = text_node.text
                    texts.append(text_content)

                    # Check for formatting
                    bold = run.find(f"{{{WORD_NAMESPACE['w']}}}b") is not None
                    italic = run.find(f"{{{WORD_NAMESPACE['w']}}}i") is not None
                    underline = run.find(f"{{{WORD_NAMESPACE['w']}}}u") is not None
                    strikethrough = run.find(f"{{{WORD_NAMESPACE['w']}}}strike") is not None

                    # Add styled run
                    if bold or italic or underline or strikethrough:
                        paragraph_data["styled_runs"].append({
                            "text": text_content,
                            "bold": bold,
                            "italic": italic,
                            "underline": underline,
                            "strikethrough": strikethrough
                        })

            if texts:
                paragraph_data["text"] = ''.join(texts)
                paragraphs.append(paragraph_data)

    return paragraphs
