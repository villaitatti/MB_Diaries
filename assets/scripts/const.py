key_id = "id"
key_index = "index"
key_page_regex_check = "page_regex"
key_offset = "offset"

key_document = "document"
key_footnote = "footnote"

footnote_fulltext = "fulltext"
footnote_permalinks = "permalinks"
footnote_type = "type"

regex_href = r'<a\s+(?:[^>]*?\s+)?href=([\"\'])(.*?)\1'
regex_footnote = r'footnote[\d]+'
regex_footnote_id = r'-{4}[\w\d]*-{4}'
regex_brackets = r'[\[\]]'

turtle_ext = 'ttl'
key_graph = 'graph'

key_body = 'body'
key_text = 'text'

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
    }
}

header_footnotes = ["Page number", "footnote id", "Last 4 words before footnote", "Footnote text", "Type", "Permalinks"]