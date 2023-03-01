#!/usr/bin/python3
import re
from nltk.stem.porter import PorterStemmer
import sys
import getopt
from queue import PriorityQueue

# Final values
stemmer = PorterStemmer()
OPERANDS_LIST = ["AND", "OR", "NOT", "(", ")"]

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


doc_id_set = {}

def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')
    global doc_id_set
    term_dictionary = {}

    with open(f'{dict_file}', 'r+') as dictionary_file:
        # Read the dictionary file as raw string
        dictionary_text = dictionary_file.read()
        # Split each line into an array
        lines = dictionary_text.split('\n')
        # Retrieve the set of document Id
        doc_id_set = eval(lines[-1])

        # Iterate through each line of the dictionary (except the last line)
        for i in range(len(lines) - 1):
            line = lines[i]
            term, doc_frequency, file_ptr_pos = line.split()
            term_dictionary[term] = (doc_frequency, file_ptr_pos)

    with open(f'{queries_file}', "r") as queries_file, open(f'{postings_file}', 'r') as postings_file,\
            open(f'{results_file}', "w") as results_file:
        # Read the queries file as raw string
        queries_text = queries_file.read()
        queries = queries_text.split('\n')
        for query in queries:
            query_results = process_query(query, term_dictionary, postings_file, doc_id_set)
            results_file.write(f'{query_results}\n')

def process_query(query, term_dictionary, postings_file, doc_id_set):
    """
    For each query, process the query and return the results (posting list)
    """
    assert len(query) <= 1024, "Query must be under 1024 characters."

    # tokenize the query
    split_query = query.split()
    split_query_without_parenthesis = []
    
    i = 0
    open_parenthesis_index = 0
    split_query_stemmed = []

    # Perform stemming on individual terms
    for token in split_query:
        if token not in OPERANDS_LIST:
            stemmer.stem(token.lower())
        split_query_stemmed.append(token)

    while i < len(split_query):
        # check for expressions in parentheses, and evaluate them
        if split_query_stemmed[i] == "(":
            open_parenthesis_index = i
            i += 1
        elif split_query_stemmed[i] == ")":
            expression = split_query_stemmed[open_parenthesis_index:i + 1]
            assert "(" not in expression, "no nested parenthesis."
            processed_expression = process_query_no_parenthesis(expression, term_dictionary, postings_file)
            split_query_without_parenthesis.append(processed_expression)
            i += 1
        # group "NOT" and the next word together (e.g. "NOT", "apple" -> ["NOT", "apple"])
        elif split_query_stemmed[i] == "NOT":
            split_query_without_parenthesis.append(split_query_stemmed[i:i + 2])
            i += 2
        else:
            # for all other cases, just add the word to the list
            split_query_without_parenthesis.append(split_query_stemmed[i])
            i += 1

    return process_query_no_parenthesis(split_query_without_parenthesis, term_dictionary, postings_file)

    return process_query_no_parenthesis(split_query_without_parenthesis, term_dictionary, postings_file, doc_id_set)

def process_or_operator(operands, term_dictionary, postings_file, doc_id_set):
    """
        Process OR operators.

        If there is a NOT operator, then the NOT operator will be the last operand.
        """
    assert len(operands) > 0, "OR operator must have at least one operand."
    
    temp_results = []
    normal_operands = []
    not_operands = []

    for operand in operands:
        if isinstance(operand, list):  # NOT operator in the form ["NOT", "word"]
            not_operands.append(operand[1])
            continue

        normal_operands.append(operand)

    while len(normal_operands) > 0:
        if len(temp_results) == 0:
            temp_results = get_postings_list(normal_operands.pop(), term_dictionary, postings_file)
            continue

        curr = normal_operands.pop()
        posting_list_curr = get_postings_list(curr, term_dictionary, postings_file)
        temp_results = union_merge(temp_results, posting_list_curr)

    # process NOT operands
    while len(not_operands) > 0:
        curr = not_operands.pop()
        posting_list_curr = get_postings_list(curr, term_dictionary, postings_file)
        negated_posting_list = posting_list_negation(list(doc_id_set), posting_list_curr)
        temp_results = union_merge(temp_results, negated_posting_list)

    return temp_results

def posting_list_negation(posting_list_all, posting_list1):
    """
    Get the postings list for the NOT operator.
    """
    result = []
    p1 = p_all = 0

    while p_all < len(posting_list_all):
        if p1 >= len(posting_list1):
            result.extend(posting_list_all[p_all:])
            break

        list1_value = None

        if isinstance(posting_list1[p1], list):
            list1_value, _ = posting_list1[p1]
        else:
            list1_value = posting_list1[p1]

        if posting_list_all[p_all] == list1_value:
            p_all += 1
            p1 += 1

        elif posting_list_all[p_all] < list1_value:
            result.append(posting_list_all[p_all])
            p_all += 1
        else: # posting_list_all[p_all] > list1_value
            p1 += 1

    return result

def union_merge(postings_list1, postings_list2):
    """
    Merge two postings lists using the union merge algorithm.
    """
    merged_postings_list = []
    p1 = p2 = 0

    while p1 < len(postings_list1) and p2 < len(postings_list2):
        list1_value = None
        list2_value = None

        if isinstance(postings_list1[p1], list):
            list1_value, _ = postings_list1[p1]
        else:
            list1_value = postings_list1[p1]

        if isinstance(postings_list2[p2], list):
            list2_value, _ = postings_list2[p2]
        else:
            list2_value = postings_list2[p2]

        if list1_value == list2_value:
            merged_postings_list.append(list1_value)
            p1 += 1
            p2 += 1
        elif list1_value < list2_value:
            merged_postings_list.append(list1_value)
            p1 += 1
        else:
            merged_postings_list.append(list2_value)
            p2 += 1

    if p1 < len(postings_list1) and p2 >= len(postings_list2):
        merged_postings_list.extend(postings_list1[p1:])

    if p2 < len(postings_list2) and p1 >= len(postings_list1):
        merged_postings_list.extend(postings_list2[p2:])

    return merged_postings_list


def process_and_operator(operands, term_dictionary, postings_file):
    """
    Process AND operators and operands.

    If there is a NOT operator, then the NOT operator will be the last operand.
    """
    pq = PriorityQueue(len(args))
    temp_results = []
    not_operands = []

    for operand in operands:
        if isinstance(operand, list): # NOT operator in the form ["NOT", "word"]
            not_operands.append(operand[1])
            continue

        # smaller doc frequency -> higher priority
        doc_frequency = int(term_dictionary[operand][0])
        pq.put(operand, 1 / doc_frequency)

    while not pq.empty():
        if len(temp_results) == 0:
            temp_results = get_postings_list(pq.get(), term_dictionary, postings_file)
            continue
        curr = pq.get()
        posting_list_curr = get_postings_list(curr, term_dictionary, postings_file)
        temp_results = intersect_merge_AND(temp_results, posting_list_curr)

    while len(not_operands) > 0:
            curr = not_operands.pop()
            posting_list_curr = get_postings_list(curr, term_dictionary, postings_file)
            temp_results = intersect_merge_NOT(temp_results, posting_list_curr)

    return temp_results

def intersect_merge_AND(postings_list1, postings_list2):
    """
    Merge two postings lists using the intersect merge algorithm with skip pointers.
    """
    merged_postings_list = []
    p1 = p2 = 0
    
    while p1 < len(postings_list1) and p2 < len(postings_list2):
        list1_value, list1_skip_ptr = None, None
        list2_value, list2_skip_ptr = None, None
        # Check if the current element in postings_list1 contains a skip pointer
        if isinstance(postings_list1[p1], list):
            list1_value, list1_skip_ptr = postings_list1[p1]
        else:
            list1_value = postings_list1[p1]

        # Check if the current element in postings_list2 contains a skip pointer
        if isinstance(postings_list2[p2], list):
            list2_value, list2_skip_ptr = postings_list2[p2]
        else:
            list2_value = postings_list2[p2]

        # Case 1: Both values in postings match 
        if list1_value == list2_value:
            merged_postings_list.append(list1_value)
            p1 += 1
            p2 += 1

        # Case 2: list1_value < list2_value
        elif list1_value < list2_value:
            if list1_skip_ptr != None and get_postings_list_value(postings_list1, list1_skip_ptr) <= list2_value:
                next_element = postings_list1[list1_skip_ptr]
                # Continuously attempt to skip
                while isinstance(next_element, list) and next_element[0] <= list2_value:
                    p1 = list1_skip_ptr
                    if isinstance(postings_list1[list1_skip_ptr], list):
                        list1_skip_ptr = next_element[1]
                        next_element = postings_list1[list1_skip_ptr]
            else:
                p1 += 1

        # Case 3: list1_value >= list2_value
        else:
            if list2_skip_ptr != None and get_postings_list_value(postings_list2, list2_skip_ptr) <= list1_value:
                next_element = postings_list2[list2_skip_ptr]
                while isinstance(next_element, list) and next_element[0] <= list1_value:
                    p2 = list2_skip_ptr
                    if isinstance(postings_list1[list1_skip_ptr], list):
                        list2_skip_ptr = next_element[1]
                        next_element = postings_list2[list2_skip_ptr]
            else:
                p2 += 1

    return merged_postings_list

def get_postings_list_value(postings_list, ptr):
    left_comparator = 0
    if isinstance(postings_list[ptr], list):
        left_comparator = postings_list[ptr][0]
    else:
        left_comparator = postings_list[ptr]
    return left_comparator

def intersect_merge_NOT(postings_list1, postings_list2):
    """
    Merge two postings list, removing the postings in postings_list2 from postings_list1.
    """
    merged_postings_list = []
    p1 = p2 = 0

    while p1 < len(postings_list1):
        list1_value, list1_skip_ptr = None, None
        list2_value, list2_skip_ptr = None, None

        if isinstance(postings_list1[p1], list):
            list1_value, list1_skip_ptr = postings_list1[p1]
        else:
            list1_value, list1_skip_ptr = postings_list1[p1], None

        if isinstance(postings_list2[p2], list):
            list2_value, list2_skip_ptr = postings_list2[p2]
        else:
            list2_value, list2_skip_ptr = postings_list2[p2], None

        # Case 1: values match
        if list1_value == list2_value:
            p1 += 1
            p2 += 1

        # Case 2: list1_value < list2_value
        elif list1_value < list2_value:
            while (isinstance(postings_list1[p1], list) and postings_list1[postings_list1[p1][1]][0] < list2_value) or postings_list1[p1] < list2_value:
                if isinstance(postings_list1[p1], list):
                    merged_postings_list.append(postings_list1[p1][1])
                else :
                    merged_postings_list.append(postings_list1[p1])
            p1 += 1
        elif list2_value < list1_value:
            while (isinstance(postings_list2[p2], list) and postings_list2[postings_list2[p2][1]][0] < list1_value) or postings_list2[p2] < list1_value:
                p2 += 1

    return merged_postings_list

def process_query_no_parenthesis(query_list, term_dictionary, postings_file):
    temp_results = []

    i = 0
    while i < len(query_list) - 1:
        if query_list[i + 1] == "AND":
            AND_operands = [query_list[i], query_list[i + 2]]
            k = 1
            while (i + 1) + 2 * k < len(query_list) and query_list[(i + 1) + 2 * k] == "AND":
                AND_operands.append(query_list[i + 2 + 2 * k])
                k += 1
            print(AND_operands)
            temp_results.append(process_and_operator(AND_operands, term_dictionary, postings_file))
            i = i + 1 + 2 * k
            continue

        temp_results.append(query_list[i])
        i += 1

    # OR_operands = [i for i in temp_results if i != "OR"]
    # if len(OR_operands) > 0:
    #     temp_results = process_or_operator(OR_operands, term_dictionary, postings_file, doc_id_set)
    return temp_results


def get_postings_list(term, term_dictionary, postings_file, temp_dict = None):
    if temp_dict and term[0] == "*":
        return temp_dict.get(term[1:])

    file_ptr_pos = term_dictionary.get(term)[1]

    # Move the file pointer to the start of the array
    postings_file.seek(int(file_ptr_pos))

    # Read the bytes from the file until the end of the line
    line_bytes = postings_file.readline()

    # Remove the newline character from the end of the line
    line_bytes = line_bytes.rstrip('\n')

    # Convert the string back to a list
    postings_list = eval(line_bytes)

    return postings_list


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

# if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None:
#     usage()
#     sys.exit(2)

run_search("dictionary.txt", "postings.txt", "queries.txt", "results.txt")