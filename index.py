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
import shutil
import sys
import getopt

import nltk
from nltk.corpus import PlaintextCorpusReader
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer

import json
import pickle

# Final values
stemmer = PorterStemmer()
BLOCK_SIZE = 2
INTERMEDIATE_FOLDER_NAME = "blocks"
def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")

def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')

    if os.path.exists(INTERMEDIATE_FOLDER_NAME):
        shutil.rmtree(INTERMEDIATE_FOLDER_NAME)
    os.makedirs(INTERMEDIATE_FOLDER_NAME)
    
    index = {}
    block_no = 0

    corpus = PlaintextCorpusReader(in_dir, '.*')
    file_ids =  corpus.fileids()
    for i, doc_id in enumerate(file_ids):
        doc = corpus.raw(doc_id)
        index_file(doc, index, os.path.splitext(doc_id)[0])
        if i % BLOCK_SIZE == BLOCK_SIZE - 1 or i == len(file_ids) - 1:
            # Exceeded block size
            write_block_to_disk(index, block_no)
            index = {}

            if i != len(file_ids) - 1:
                block_no += 1
        
    merged_dictionary = merge_blocks_on_disk(0, block_no)
    print(merged_dictionary)
    # write_dictionary_and_postings_to_disk()

def index_file(doc, index, doc_id):
    sentences = sent_tokenize(doc)
    for sentence in sentences:
        words = word_tokenize(sentence)
        stemmed_words = [stemmer.stem(word.lower()) for word in words]
        for i, word in enumerate(stemmed_words):
            if word in index:
                if doc_id not in index[word]["postings_list"]:
                    index[word]["doc_freq"] += 1
                    index[word]["postings_list"].append(doc_id)
            else:
                index[word] = {
                    "postings_list": [doc_id],
                    "doc_freq": 1
                }

def write_block_to_disk(index, block_no):
    with open("blocks" + f'/{block_no}', 'w') as f:
        sorted_index = sorted(index.items())
        output_dict = {term: values for term, values in sorted_index}
        output_line = json.dumps(output_dict)
        f.write(output_line)

# 2
# 0 1

def merge_blocks_on_disk(start, end):
    if end - start >= 1:
        mid = (start + end) // 2
        merged_dictionary = merge(merge_blocks_on_disk(start, mid), merge_blocks_on_disk(mid+1, end))
        return merged_dictionary
    else:
        return start


def merge(left, right):
    left_dictionary = {}
    right_dictionary = {}
    merged_dictionary = {}

    with open("blocks" + f'/{left}', 'r') as file1, open("blocks" + f'/{right}', 'r') as file2:
        left_dictionary = json.load(file1)
        right_dictionary = json.load(file2)
    
    for term, prop in right_dictionary.items():
        if term in left_dictionary:
            # if a term in right_dictionary can be found in left_dictionary, 
            # merge the posting list, increment document frequency and add the term into merged_dictionary
            left_posting_list = left_dictionary[term]["postings_list"]
            right_posting_list = prop["postings_list"]
            left_freq = left_dictionary[term]["doc_freq"]
            right_freq = prop["doc_freq"]
            merged_posting_list = sorted(left_posting_list + right_posting_list)
            merged_dictionary[term] = {
                    "postings_list": merged_posting_list,
                    "doc_freq": left_freq + right_freq
                }
        else:
            # if a term in right_dictionary cannot be found in left_dictionary, add the term to merged_dictionary
            merged_dictionary[term] = prop
    
    for term, prop in left_dictionary.items():
        if term not in merged_dictionary:
            # if a term in left_dictionary cannot be found in merged_dictionary, add the term into to merged_dictionary
            merged_dictionary[term] = prop
    
    return merged_dictionary


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
