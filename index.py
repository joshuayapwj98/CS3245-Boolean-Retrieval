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

import math

import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer

import json

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

    global BLOCK_SIZE
    if in_dir == './sample_training_folder':
        BLOCK_SIZE = 1

    print('start of indexing')

    if os.path.exists(INTERMEDIATE_BLOCK):
        shutil.rmtree(INTERMEDIATE_BLOCK)
    os.makedirs(INTERMEDIATE_BLOCK)

    index = {}
    global block_no
    doc_id_set = set()

    files = os.listdir(in_dir)
    
    print('Creating intermediate blocks...')
    # Iterate through all the files and construct intermediate blocks
    for i, file_name in enumerate(files):
        document = ''
        with open(f'{in_dir}/{file_name}', 'r') as file:
            document = file.read()
        doc_id = int(os.path.splitext(file_name)[0])
        doc_id_set.add(doc_id)
        index_file(document, index, doc_id)
        if i % BLOCK_SIZE == BLOCK_SIZE - 1 or i == len(files) - 1:
            # Exceeded block size
            write_block_to_disk(index, block_no)
            index = {}
            if i != len(files) - 1:
                block_no += 1
   
    print('Merging intermediate blocks...')
    # Merge intermediate blocks into the final block
    final_block_no = merge_blocks_on_disk(0, block_no)
    
    print('Writing to output directories...')
    # Write final block into dictionary and postings file respectively
    write_dictionary_postings_to_disk(final_block_no, out_dict, out_postings, doc_id_set)

    print('End of indexing')

def index_file(doc, index, doc_id):
    # Get sentences in each document
    sentences = sent_tokenize(doc)
    for sentence in sentences:
        # Get each word in a sentence
        words = word_tokenize(sentence)
        # Perform stemming
        stemmed_words = [stemmer.stem(word.lower()) for word in words]
        for i, word in enumerate(stemmed_words):
            if word in index:
                # Current word exist in the index
                if doc_id not in index[word]:
                    # Since the word does not contain the documentId, append it to the list 
                    index[word].append(doc_id)
            else:
                # Current word does not exist in the index
                index[word] = [doc_id]
         
def write_block_to_disk(index, block_no):
    with open("blocks" + f'/{block_no}', 'w') as f:
        # Sort the intermediate block dictionary
        sorted_index = sorted(index.keys())
        # Get same key-value pairs as index but with the keys sorted in lexicographic order
        output_dict = {term: index[term] for term in sorted_index}
        # Transform the output type to write into the intermediate block
        output_line = json.dumps(output_dict)
        f.write(output_line)

def merge_blocks_on_disk(start, end):
    if end - start >= 1:
        mid = (start + end) // 2
        left = merge_blocks_on_disk(start, mid)
        right = merge_blocks_on_disk(mid+1, end)
        merged_block_no = merge(left, right)
        return merged_block_no
    else:
        # Base case
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

    # Removes the two intermediate blocks
    os.remove(INTERMEDIATE_BLOCK + f'/{left}')
    os.remove(INTERMEDIATE_BLOCK + f'/{right}')

    # return the index of the new merged block
    return block_no
    
def write_dictionary_postings_to_disk(number, out_dict, out_postings, doc_id_set):
    merged_dictionary = {}

    block_file_dir = INTERMEDIATE_BLOCK + f'/{number}'
    with open(block_file_dir, 'r') as block_file, open(f'{out_dict}', 'w') as dictionary_file, open(f'{out_postings}', 'w') as postings_file:
        merged_dictionary = json.load(block_file)
        file_ptr_pos = 0
        for term, postings_list in merged_dictionary.items():

            new_postings_list = str(get_skip_pointers(postings_list))
            # write the current term
            postings_file.write(term + " ")
            # Get the starting position of the list
            file_ptr_pos = postings_file.tell()
            # Write the list to the file
            postings_file.write(new_postings_list)
            # Move the file_ptr_pos to the starting position of the array that was just written
            postings_file.seek(file_ptr_pos + len(new_postings_list))
            # Write a new line for the next dictionary entry
            postings_file.write("\n")

            # Add the file_ptr_pos reference for each term for quick access
            dictionary_file.write(term + " " + str(len(new_postings_list)) + " " + str(file_ptr_pos) + "\n")
        
        dictionary_file.write(str(doc_id_set))

def get_skip_pointers(postings_list):
    postings_list_builder = []
    if len(postings_list) == 1:
        postings_list_builder.append(postings_list[0])
    else:
        # Calculate the number of skip pointers by perform sqrt() of the postings list length
        skip_pointer_counter = math.isqrt(len(postings_list))
        # Calculate the average skip distance
        skip_distance = math.floor(len(postings_list) / skip_pointer_counter)
        # Iterate through each documentId in postings_list
        for i in range(len(postings_list)):
            # Check for the neccessary conditions for a skip pointer
            if i % skip_distance == 0 and i + skip_distance < len(postings_list):
                # Append the current documentId (value of i) to the previous idx element
                postings_list_builder.append([postings_list[i], i + skip_distance])
                skip_pointer_counter -= 1
            elif i % skip_distance == 0 and i + skip_distance >= len(postings_list):
                # Append the current documentId (value of i) to the last idx of postings_list
                postings_list_builder.append([postings_list[i], len(postings_list) - 1])
                skip_pointer_counter -= 1
            else:
                # By default, an element in the postings_list will be a element
                postings_list_builder.append(postings_list[i])
        
        if skip_pointer_counter > 0:
            print(f"Error. There is a total of {skip_pointer_counter} not being used...")

    return postings_list_builder

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