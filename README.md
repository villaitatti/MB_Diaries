# MB_Diaries

Execute with:

```
Usage: archipelago_xml_data.py [OPTIONS]

Options:
  -d TEXT  Diaries to iterate. -d 1933 [-d 1933]  [required]
  -u       Execute the upload
  --help   Show this message and exit.
```

## Example query via OPENAI

```
Given the following text, return a JSON of artworks, places, and people only like this: [{"artwork name":{"offset": 10,"paragraph" : 1}}, ...].
where artwork is the name of the artwork, offset is the number of characters from the start of the paragraph, and paragraph is the index of the paragraph starting from 1. Response with nothig other than json file.
here is the text:
[Aug. 7- Oct. 24, 1891: Mary and Bernhard travel together from Antwerp to Venice]

x 〈Friday,〉August 7, 1891, Antwerp

Discussed difference between Belgians and Hollanders. Is it due to the hold of the Catholic Church in Belgium? 

Read L’Intruse by Maeterlingk, [sic] and compared it with Mrs. Augusta Webster’s Auspicious Day.
```


```
"""
# Add Locations found in pages only for 1891
if diary == '1891':
  input_locations = os.path.join(input_path, 'notes', '1891_Locations.csv')

  # Store WKT value
  for i, row in pd.read_csv(input_locations).iterrows():
    page = row[const.diaries[diary][const.key_footnote_header_page]]

    location_wkt = row[const.diaries[diary][const.key_footnote_header_location_wkt]]
    location_name = row[const.diaries[diary][const.key_footnote_header_location_name]]
    location_link = f'https://www.wikidata.org/wiki/{row[const.diaries[diary][const.key_footnote_header_location_link]]}'
    
    # If there is no wkt, break
    if location_wkt is None:
      break
      
    # Append wkt value
    pages[page][const.key_footnote_header_location_wkt] = location_wkt
    pages[page][const.key_footnote_header_location_name] = location_name 
    pages[page][const.key_footnote_header_location_link] = location_link
"""
```


Regex to remove empty lines `^\s*$\n` 
Regex to get [p.] and update in new line: `(?<=.)(\[p[\d]{2,3}\])` and replace with `\n$1`
Regex to prepend notation to days 

*`^(?!\$\$HEADER\$\$_)(.*?\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})`
*`^(?!\$\$HEADER\$\$_)(.*?\b(?:Jan.|Feb.|Mar.|Apr.|May|June|Jul.|Aug.|Sept.|Oct.|Nov.|Dec.)\s+\d{1,2},\s+\d{4})`

Replace `<>` with `[]`