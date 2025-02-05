key_id = "id"
key_index = "index"
key_page_regex_check = "page_regex"
key_offset = "offset"

key_note_header = '$$HEADER$$_'

key_paragraph = "p"
key_header = "h3"

key_document = "document"
key_footnote = "footnote"
key_notes_dir = "notes"
key_manifest_dir = "manifests"

key_title = "title"

footnote_annotator = "annotator"
footnote_fulltext = "fulltext"
footnote_permalinks = "permalinks"
footnote_type = "type"
footnote_index = 'index'
footnote_start = 'start'
footnote_end = 'end'

regex_href = r'<a\s+(?:[^>]*?\s+)?href=([\"\'])(.*?)\1'
regex_footnote = r'footnote[\d]+'
regex_footnote_id = r'-{4}[\w\d]*-{4}'
regex_brackets = r'[\[p\]]'
regex_date = r'(\b\d{1,2}\D{0,3})?\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?)\D?(\d{1,2}\D?)?\D?((18[7-9]\d|20\d{2})|\d{2})'

turtle_ext = 'ttl'
key_graph = 'graph'

key_body = 'body'
key_text = 'text'
key_type = 'type'
key_date = 'date'
key_paragraphs = 'content'
key_metadata = 'metadata'

key_object = 'object'
key_predicate = 'predicate'

key_upload_username = 'username'
key_upload_password = 'password'
key_upload_endpoint = 'endpoint'

IIIF_server = 'https://ids.lib.harvard.edu/ids/iiif/'
IIIF_trailer = '/full/full/0/default.jpg'

diary_data = {
    "1891": {
        key_id: 420756309,
        key_page_regex_check: r'\[\s*\d+\s*[\s\w\,\’\‘]{3,}\]',
        key_title: "Diary 1, August 1891 - November 1893",
    },
    "1915": {
        key_id: 491567726,
        key_page_regex_check: r'\[[0-9]+\][\s]*'
    },
    "1927": {
        key_id: 491567726,
        key_page_regex_check: r'^[\s]*\[[0-9]+\][\s]*$'
    },
    "1933": {
        key_id: 493343490,
        key_page_regex_check: r'^[\s]*\[[0-9]+\][\s]*'
    },
    "1903": {
        key_id: 493312270,
        key_page_regex_check: r'\[\s*\d+\s*\]'
    },
    "1894-95": {
        key_id: 420765526,
        key_page_regex_check: r'\[\s*\d+\s*\]'
    },
    "1895": {
        key_id: 493295736,
        key_page_regex_check: r'\[\s*\d+\s*[\s\w\,\’\‘\.]*\]'
    },
    "1897": {
        key_id: 420766084,
        key_page_regex_check: r'\[\s*\d+\s*[\s\w\,\’\‘\.]*\]'
    }
}

key_footnote_header_page = "Page number"
key_footnote_header_id = "footnote id"
key_footnote_header_before = 'Last 4 words before footnote'
key_footnote_header_permalinks = 'Permalinks'
key_footnote_header_type = "Type"
key_footnote_header_value = "Value"
key_footnote_header_paragraph = "Paragraph"
key_footnote_header_start = "Start"
key_footnote_header_end = "End"
key_footnote_header_annotator = "Annotator"
key_footnote_header_location_wkt = 'location_wkt'
key_footnote_header_location_name = 'location_name'
key_footnote_header_location_link = 'location_link'

header_footnotes = [key_footnote_header_page, key_footnote_header_id, key_footnote_header_before,
                    "Footnote text", key_footnote_header_type, key_footnote_header_permalinks]

note_header_page = 'Diary Page'
note_header_entity = 'Entity (Value)'
note_header_authority = 'Authority Name'
note_header_number = 'Entity No.'
note_header_type = 'Entity Type'
note_header_descriptor = "Note 1 Descriptor"
note_header_context = "Note 2 Context"
note_header_disambiguation1 = "DIsambiguation URL 1"
note_header_disambiguation2 = "DIsambiguation URL 2"
note_header_disambiguation3 = "DIsambiguation URL 3"


diaries = {
  "1891": {
    key_footnote_header_page: 'Page #',
    key_footnote_header_type: 'Type',
    key_footnote_header_value: 'Entry',
    key_footnote_header_paragraph: 'Paragraph #',
    key_footnote_header_start: 'Start',
    key_footnote_header_end: 'End',
    key_footnote_header_annotator: 'Annotator',
    key_footnote_header_permalinks: 'Wikidata ID',
    key_footnote_header_location_wkt: 'WKT',
    key_footnote_header_location_name: 'Entry',
    key_footnote_header_location_link: 'Wikidata ID'
  }
}

KEY_VALUE = 'value'
KEY_TYPE = 'type'
KEY_TEXT = 'text'
KEY_RUNS = 'runs'

KEY_BOLD = 'bold'
KEY_ITALIC = 'italic'
KEY_UNDERLINE = 'underline'
KEY_STRIKE = 'strike'

KEY_START_POSITION = 'start_position'
KEY_END_POSITION = 'end_position'

regex_page_pattern = r'\[p?\d+[^\]]*\]'