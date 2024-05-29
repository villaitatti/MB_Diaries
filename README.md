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

## Clean .txt diaries

Cleaning the diaries is a semi-automatic process. I am following these steps:

1. Detect page notations and separate them from paragraphs:
    * find notations with `(\[0+[\d]+\])` and replace with `\n$1\n`
    * prepend character p to the number
        * find `[00` and replace with `[p`
        * find `[0` and replace with `[p`
    * check if some notations have been changed already
        * Use `(?<=.)(\[p[\d]{2,3}\])` and update accordingly (e.g., add new line before or after)
2. Check notation after notation using `\[p[\d]{2,3}\]` and check if something is missing 
3. Remove empty lines finding `^\s*$\n` and replacing with empty line
4. Find lines denoting days using the following regex and replace with `$$$HEADER$$$_$1`:
    * `^(?!\$\$HEADER\$\$_)(.*?\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})`
    * `^(?!\$\$HEADER\$\$_)(.*?\b(?:Jan.|Feb.|Mar.|Apr.|May|June|Jul.|Aug.|Sept.|Oct.|Nov.|Dec.)\s+\d{1,2},\s+\d{4})`
    * if needed update regex to match diary cases (e.g., Jun. instead of June)
5. Find and replace `<` and `>` with `[` and `]`