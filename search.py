#!/usr/bin/python3
import re
import nltk
import sys
import getopt
from queue import PriorityQueue


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')
    # This is an empty method
    # Pls implement your code in below

    # Open the dictionary file and postings file

    # logic to rearrange order of operations,
    # https://en.wikipedia.org/wiki/Binary_expression_tree

    # corner cases
    # operators not in upper case


def process_query(query):
    # tokenize the query
    split_query = query.split()
    split_query_parenthesis_processed = []

    i = 0
    open_parenthesis_index = 0
    close_parenthesis_index = 0
    while i < len(split_query):
        if split_query[i] == "(":
            open_parenthesis_index = i
            i += 1
            continue
        if split_query[i] == ")":
            parenthesis_expression = split_query[open_parenthesis_index:i + 1]
            processed_expression = process_parenthesis(parenthesis_expression)
            split_query_parenthesis_processed.append(processed_expression)
            i += 1
            continue
        if split_query[i] == "NOT":
            split_query_parenthesis_processed.append(split_query[i:i + 2])
            i += 2
            continue
        split_query_parenthesis_processed.append(split_query[i])
        i += 1


def process_parenthesis(parenthesis_expression):
    return process_query_no_parenthesis(parenthesis_expression)


def process_or_operator(operands):
    temp_results = []

    # TODO : OR merging
    # for operand in args:
    # or merging

    return temp_results


def process_and_operator(operands):
    pq = PriorityQueue(len(args))
    temp_results = []

    for operand in operands:
        if isinstance(operand, list):
            pq.put((0, operand))
            continue

        # TODO: get the doc_frequency from the dictionary
        doc_frequency = 99
        pq.put(1 / dict.get(), operand)

    while not pq.empty():
        curr = pq.get()
        # TODO: get postings list from postings file and merge


def process_query_no_parenthesis(query_list):
    temp_results = []

    i = 0
    while i < len(query_list):
        if query_list[i] == "AND":
            AND_operands = query_list[i - 1]
            AND_operands.append(query_list[i + 1])
            k = 1
            while i + 2 * k < len(query_list) and query_list[i + 2 * k] == "AND":
                AND_operands.append(query_list[i + k])
                k += 1
            temp_results.append(process_and_operator(AND_operands))
            i = i + 2 * k
            continue

        temp_results.append(query_list[i])
        i += 1

    OR_operands = [i for i in temp_results if i != "OR"]
    return process_or_operator(OR_operands)


def get_postings_list(term, temp_dict, actual_positings):
    if term[0] == "*":
        return temp_dict.get(term[1:])

    # get postings list from postings file
    # remove punctuations
    # remove stop words
    # stem the words / lemmatize
    # return the list of tokens
    "bill OR Gates AND (vista OR XP) AND NOT mac"


dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None:
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
