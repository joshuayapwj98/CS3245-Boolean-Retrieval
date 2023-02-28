#!/usr/bin/python3


"""
Different commands depending on environment
Debug phase:
python3 index.py -i ./sample_training_folder -d dictionary.txt -p postings.txt

Build phase:
Note: need to find directory to where the reuters data set is installed on your local machine

Jun Wei (MacOS):
python3 index.py -i /Users/tanju/nltk_data/corpora/reuters/training -d dictionary.txt -p postings.txt

Joshua (MacOS):
python3 index.py -i /Users/joshuayap/nltk_data/corpora/reuters/training -d dictionary.txt -p postings.txt
"""

import re
import os
import shutil
import sys
import getopt

import linecache
import math

import nltk
from nltk.corpus import PlaintextCorpusReader
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer

import json
import pickle

# Final values
stemmer = PorterStemmer()
BLOCK_SIZE = 2000
INTERMEDIATE_BLOCK = "blocks"

# global variables
block_no = 0


def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')

    if os.path.exists(INTERMEDIATE_BLOCK):
        shutil.rmtree(INTERMEDIATE_BLOCK)
    os.makedirs(INTERMEDIATE_BLOCK)

    index = {}
    global block_no

    corpus = PlaintextCorpusReader(in_dir, '.*')
    file_ids = corpus.fileids()
    for i, doc_id in enumerate(file_ids):
        doc = corpus.raw(doc_id)
        index_file(doc, index, int(os.path.splitext(doc_id)[0]))
        if i % BLOCK_SIZE == BLOCK_SIZE - 1 or i == len(file_ids) - 1:
            # Exceeded block size
            write_block_to_disk(index, block_no)
            index = {}
            if i != len(file_ids) - 1:
                block_no += 1

    final_block_no = merge_blocks_on_disk(0, block_no)
    write_dictionary_postings_to_disk(final_block_no, out_dict, out_postings)


def index_file(doc, index, doc_id):
    sentences = sent_tokenize(doc)
    for sentence in sentences:
        words = word_tokenize(sentence)
        stemmed_words = [stemmer.stem(word.lower()) for word in words]
        for i, word in enumerate(stemmed_words):
            if word in index:
                if doc_id not in index[word]:
                    index[word].append(doc_id)
            else:
                index[word] = [doc_id]


def write_block_to_disk(index, block_no):
    with open("blocks" + f'/{block_no}', 'w') as f:
        sorted_index = sorted(index.items())
        output_dict = {term: values for term, values in sorted_index}
        output_line = json.dumps(output_dict)
        f.write(output_line)


def merge_blocks_on_disk(start, end):
    if end - start >= 1:
        mid = (start + end) // 2
        left = merge_blocks_on_disk(start, mid)
        right = merge_blocks_on_disk(mid + 1, end)
        merged_block_no = merge(left, right)
        return merged_block_no
    else:
        return start


def merge(left, right):
    global block_no

    left_dictionary = {}
    right_dictionary = {}
    merged_dictionary = {}

    with open(INTERMEDIATE_BLOCK + f'/{left}', 'r') as file1, open(INTERMEDIATE_BLOCK + f'/{right}', 'r') as file2:
        left_dictionary = json.load(file1)
        right_dictionary = json.load(file2)

    for term, prop in right_dictionary.items():
        if term in left_dictionary:
            # if a term in right_dictionary can be found in left_dictionary, 
            # merge the posting list, increment document frequency and add the term into merged_dictionary
            left_posting_list = left_dictionary[term]
            right_posting_list = prop
            merged_posting_list = sorted(left_posting_list + right_posting_list)
            merged_dictionary[term] = merged_posting_list
        else:
            # if a term in right_dictionary cannot be found in left_dictionary, add the term to merged_dictionary
            merged_dictionary[term] = prop

    for term, prop in left_dictionary.items():
        if term not in merged_dictionary:
            # if a term in left_dictionary cannot be found in merged_dictionary, add the term into to merged_dictionary
            merged_dictionary[term] = prop

    block_no += 1

    # write the merged dictionary to a new block on disk
    with open(INTERMEDIATE_BLOCK + f'/{block_no}', 'w') as f:
        output_line = json.dumps(merged_dictionary)
        f.write(output_line)

    os.remove(INTERMEDIATE_BLOCK + f'/{left}')
    os.remove(INTERMEDIATE_BLOCK + f'/{right}')

    # return the index of the new merged block
    return block_no


def write_dictionary_postings_to_disk(number, out_dict, out_postings):
    merged_dictionary = {}

    block_file_dir = INTERMEDIATE_BLOCK + f'/{number}'
    with open(block_file_dir, 'r') as block_file, open(f'{out_dict}', 'w') as dictionary_file, open(f'{out_postings}',
                                                                                                    'w') as postings_file:
        merged_dictionary = json.load(block_file)
        line_no = 1
        for term, postings_list in merged_dictionary.items():
            sqrt_val = math.sqrt(len(postings_list))
            skip_pointers_no = math.floor(sqrt_val)
            skip_distance = math.floor(int(len(postings_list) / skip_pointers_no))
            new_postings_list = []
            next_index = 0
            for i in range(len(postings_list)):
                new_postings_list.append([postings_list[i]])
                if skip_pointers_no != 0:
                    if i == 0 or i == next_index:
                        next_index = i + skip_distance - 1
                        new_postings_list[i].append(postings_list[next_index])
                        skip_pointers_no -= 1

            postings_file.write(term + " " + str(new_postings_list) + "\n")
            dictionary_file.write(term + " " + str(len(new_postings_list)) + " " + str(line_no) + "\n")
            line_no += 1


input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i':  # input directory
        input_directory = a
    elif o == '-d':  # dictionary file
        output_file_dictionary = a
    elif o == '-p':  # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
