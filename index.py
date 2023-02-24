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

            for word in words:
                stemmed_word = stemmer.stem(word.lower())
                # Add the stemmed token to the index
                if stemmed_word not in index:
                    index[stemmed_word] = []
                if doc_id not in index[stemmed_word]:
                    index[stemmed_word].append(doc_id)
    
    # Write the index to a file called dictionary.txt
    with open(out_dict, 'w') as f:
        for i, (key, value) in enumerate(index.items(), 1):
            f.write(f"{key}:{i}\n")

    # Create a posting list file called postings.txt
    with open(out_postings, 'w') as f:
        # Loop over the index and write each posting list to the file
        for term, posting_list in index.items():
            posting_list_str = ','.join(os.path.splitext(posting)[0] for posting in posting_list)
            f.write(f"{term}:{posting_list_str}\n")


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
