import pandas as pd
import uuid
import os

cur_path = os.path.dirname(os.path.realpath(__file__))

notes_1891 = os.path.join(cur_path, '1891_people.tsv')
df = pd.read_csv(notes_1891, encoding='utf-8', sep='\t')

min_limit = 73
max_limit = 176

# Define constant for column name
PAGE_COLUMN = 'Page #'

# create df with only the rows with column type person, with Wikidata ID and with page number between min and max
df = df[(df['Type'] == 'person') & (df['Wikidata ID'] != 'None') & (df[PAGE_COLUMN] >= min_limit) & (df[PAGE_COLUMN] <= max_limit)]

# Order dataframe by Page #
notes_1891_ordered = df.sort_values(by=[PAGE_COLUMN], ascending=True)
notes_1891_ordered.to_csv(os.path.join(cur_path,'1891_ordered.csv'))