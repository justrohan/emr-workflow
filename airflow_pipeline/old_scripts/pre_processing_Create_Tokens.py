#!/usr/bin/env python

"""
Tokenize raw EMR data to support downstream feature engineering tasks
input: raw EMR notes
output: tokenized notes (json)
Last updated: 1.24.20
Author: Andrew Malinow
"""

"""
imports
"""
import json
import nltk
from nltk.corpus import wordnet as wn
from nltk import word_tokenize
import requests
import string
import re
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

"""
global variables
"""
outputfile='emr_tokens.parquet'

nltk.download('stopwords')
nltk.download('punkt')
en_stop = set(nltk.corpus.stopwords.words('english'))


def get_data():
    resp = requests.get('http://10.32.22.16:56733/noteevents/55500')
    if resp.status_code != 200:
        raise ApiError('GET /noteevents/<size> {}'.format(resp.status_code))
    json_notes=resp.json()['json_notes']
    #gets rid of new line characters "\n", more performant thatn re.sub():
    data = [x['text'].translate(string.punctuation) for x in json_notes]
    #gets rid of other special characters in the text
    data = [re.sub('\'','',x) for x in data]
    data = [re.sub(r'([^\s\w]|_)+','',x) for x in data]
    return data

"""
Data Prep Functions
prepare text for topic modeling
"""
def prepare_text_for_lda(text):
    tokens = word_tokenize(text)
    tokens = [token for token in tokens if len(token) > 3]
    tokens = [token for token in tokens if token not in en_stop]
    return tokens

"""
write tokens to json
"""
def write_tokens(token_list):
    df = pd.DataFrame({'token_list': token_list})
    table = pa.Table.from_pandas(df)
    pq.write_table(table, outputfile)
        

"""
tokenize data
"""
def tokenize_data():
    data = get_data()
    #change the data list to a string and get rid of the list notation in the new string
    string_data = str(data)
    string_data = re.sub(',', '', string_data)
    string_data = re.sub('\[', '', string_data)
    string_data = re.sub(']', '', string_data)
    tokens=prepare_text_for_lda(string_data)
    write_tokens(tokens)

