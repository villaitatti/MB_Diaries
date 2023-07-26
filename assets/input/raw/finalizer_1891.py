import os
import pandas as pd
import requests

# Header bot required https://meta.wikimedia.org/wiki/User-Agent_policy
wikidata_url = 'https://query.wikidata.org/sparql'
wikidata_headers = {'User-Agent': 'CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org)'}


input1 = os.path.join(os.path.dirname(__file__), 'Annotations - Annotations People and Places (NER) - Diary [1].csv')

output1 = os.path.join(os.path.dirname(__file__), 'Locations.csv')

df1 = pd.read_csv(input1)

# Get only rows with column Type = 'location'
df2 = df1[df1['Type'] == 'location']
df2.where(df2.notnull(), None)


for i, row in df2.iterrows():
  if row['Wikidata ID'] is None:
    break

  uri = f'wd:{row["Wikidata ID"]}'
  query = 'select ?s ?wkt{ ?s p:P625 ?coordinate.?coordinate ps:P625 ?wkt.BIND(' + uri + ' as ?s) }'
  
  # Execute request against wikidata and save its result
  try:
    response = requests.get(wikidata_url, params={'query': query, 'format': 'json'}, headers=wikidata_headers)
    response_json = response.json()
    wkt = response_json['results']['bindings'][0]['wkt']['value']

  # Otherwise, set wkt to None
  except (IndexError, requests.exceptions.JSONDecodeError) as ex:
    wkt = None
    print(ex)
  
  finally:
    df2.at[i, 'WKT'] = wkt
    
# Save dataframe to csv 
df2.to_csv(output1, index=False)