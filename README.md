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