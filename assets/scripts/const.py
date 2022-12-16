key_id = "id"
key_index = "index"
key_page_regex_check = "page_regex"
key_offset = "offset"

key_document = "document"
key_footnote = "footnote"

footnote_fulltext = "fulltext"
footnote_permalinks = "permalinks"
footnote_type = "type"
footnote_index = 'index'
footnote_start = 'start'
footnote_end = 'end'

regex_href = r'<a\s+(?:[^>]*?\s+)?href=([\"\'])(.*?)\1'
regex_footnote = r'footnote[\d]+'
regex_footnote_id = r'-{4}[\w\d]*-{4}'
regex_brackets = r'[\[\]]'

turtle_ext = 'ttl'
key_graph = 'graph'

key_body = 'body'
key_text = 'text'
key_paragraphs = 'paragraphs'

key_upload_username = 'username'
key_upload_password = 'password'
key_upload_endpoint = 'endpoint'

IIIF_server = 'https://ids.lib.harvard.edu/ids/iiif/'
IIIF_trailer = '/full/full/0/default.jpg'

diary_data = {
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
    "1894-95": {
      key_id: 420765526,
      key_page_regex_check: r'\[\s*\d+\s*\]'
    }
}

key_footnote_header_page = "Page number"
key_footnote_header_id = "footnote id"
key_footnote_header_before = 'Last 4 words before footnote'
key_footnote_header_permalinks = 'Permalinks'
key_footnote_header_type = "Type"

header_footnotes = [key_footnote_header_page, key_footnote_header_id, key_footnote_header_before, "Footnote text", key_footnote_header_type, key_footnote_header_permalinks]