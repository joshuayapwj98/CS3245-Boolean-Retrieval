#!/usr/bin/python3



"""
Different commands depending on environment
Debug phase:
python3 index.py -i ./sample_training_folder -d dictionary.txt -p postings.txt

Build phase:
Note: need to find directory to where the reuters data set is installed on your local machine

Jun Wei:


Joshua (MacOS):
python3 index.py -i /Users/joshuayap/nltk_data/corpora/reuters/training -d dictionary.txt -p postings.txt
"""

import re
import os
import sys
import getopt

import nltk
from nltk.corpus import PlaintextCorpusReader
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer

import json
import pickle

stemmer = PorterStemmer()

def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")

def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')
    
    corpus = PlaintextCorpusReader(in_dir, '.*')

    index = {}

    for doc_id in corpus.fileids():
        doc = corpus.raw(doc_id)
        # Get setences in each document.
        sentences = sent_tokenize(doc)
        
        for sentence in sentences:
            # Tokenize the sentence into words.
            words = word_tokenize(sentence)
            stemmed_words = [stemmer.stem(word.lower()) for word in words]

            for i, token in enumerate(stemmed_words):
                if token not in index:
                    # Add a new entry to the index for the token
                    index[token] = {'freq': 0, 'postings': {}}
                # Increment the frequency count for the token
                index[token]['freq'] += 1
                doc_id = os.path.splitext(doc_id)[0]
                if doc_id not in index[token]['postings']:
                    # Add a new entry to the postings list for the document
                    index[token]['postings'][doc_id] = []
                # Append the position of the token in the document to the postings list
                index[token]['postings'][doc_id].append(i)
    
    # Write the index to a file called dictionary.txt
    with open(out_dict, 'w') as f:
        for i, (key, value) in enumerate(index.items(), 1):
            f.write(f"{key}:{i}\n")

    # Create a posting list file called postings.txt
    with open(out_postings, 'w') as f:
        for token, data in index.items():
            f.write(f"{token}:{data['freq']} | {json.dumps(data['postings'])}\n")


input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i': # input directory
        input_directory = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
