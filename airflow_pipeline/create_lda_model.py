import pandas as pd
from nltk import sent_tokenize
import re
import pickle
import pymongo
import gridfs
import datetime
from workflow_read_and_write import standard_read_from_db, lda_write_to_db 

#table = pq.read_table('/home/emrm1/emr-workflow/admissions.parquet')
#df = table.to_pandas()

#notes_list = df['notes'].tolist()

#all_notes_text = ''
#for note in notes_list:
#    all_notes_text += ' ' + note.replace('\n','')

#new_sentences = sent_tokenize(all_notes_text)

def generate_ngrams(s, n):
    # Convert to lowercases
    s = s.lower()
    # Break sentence into tokens, remove empty tokens
    tokens = [token for token in s.split(" ") if token != ""]
    tokens = [token for token in s.split(" ") if len(token)>=3]
    # Use the zip function to help us generate n-grams
    # Concatentate the tokens into ngrams and return
    ngrams = zip(*[tokens[i:] for i in range(n)])
    return ["_".join(ngram) for ngram in ngrams]

def create_ngram_tokens(notes):
    new_sentences = sent_tokenize(notes)
    all_ngrams=[]
    for sentence in new_sentences:
        sentence_ngrams=generate_ngrams(sentence, 5)
        all_ngrams+=sentence_ngrams
    ngrams_concat_tokens = [[ngram] for ngram in all_ngrams]
    return ngrams_concat_tokens

def make_model(tokens):
    #create corpus, dictionary, and lda model
    dictionary = gensim.corpora.Dictionary(tokens)
    corpus = dictionary.doc2bow(tokens)
    #the statement below doesn't work, changed input to ngram_concat_tokens
    #corpus = [dictionary.doc2bow(text) for text in all_ngrams]
    lda_model=gensim.models.LdaMulticore(corpus=corpus,num_topics=5,id2word=dictionary,passes=10,workers=3)

    return dictionary, corpus, lda_model

def create_lda_model():
    notes = standard_read_from_db('all_notes_cleansed').decode()
    tokens = create_ngram_tokens(notes)
    dictionary, corpus, lda_model = make_model(tokens)
    lda_write_to_db(dictionary, corpus, lda_model)

