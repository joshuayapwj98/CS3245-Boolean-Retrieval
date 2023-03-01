#!/usr/bin/python3
import re
from nltk.stem.porter import PorterStemmer
import sys
import getopt

# Final values
stemmer = PorterStemmer()

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

ops_dict = {'OR': 0, 'AND': 1, 'NOT': 2}

doc_id_set = {}

def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')
    global doc_id_set
    term_dictionary = {}
    set_idx = 0

    with open(f'{dict_file}', 'r+') as dictionary_file:
        # Read the dictionary file as raw string
        dictionary_text = dictionary_file.read()
        # Split each line into an array
        lines = dictionary_text.split('\n')
        # Retrieve the set of document Id

        # Iterate through each line of the dictionary (except the last line)
        for i in range(len(lines)):
            line = lines[i]
            term, doc_frequency, file_ptr_pos = line.split()
            term_dictionary[term] = (doc_frequency, file_ptr_pos)

    with open(f'{queries_file}', "r") as queries_file, open(f'{postings_file}', 'r') as postings_file,\
            open(f'{results_file}', "w") as results_file:
        # Read the queries file as raw string
        
        doc_id_set = list(get_postings_list('all_dict', term_dictionary, postings_file))

        queries_text = queries_file.read()
        queries = queries_text.split('\n')
        for i, query in enumerate(queries):
            post_fix = get_postfix(query)
            query_results = process_query(post_fix, term_dictionary, postings_file, doc_id_set)
            string_builder = ''
            for id in query_results:
                if type(id) == list:
                    string_builder = ' '.join(str(i) for i in id)
                else:   
                    string_builder += str(id) + " "
            string_builder.strip()
            results_file.write(string_builder)
            if i < len(queries) - 1:
                results_file.write("\n")

def get_postfix(infix):
    """Convert an infix expression to RPN using the Shunting Yard algorithm."""
    # Define operator precedence

    # Initialize stack and queue
    operators = []
    postfix = []
    global ops_dict

    # Split the infix expression into tokens
    tokens = split_string(infix)

    for token in tokens:
        if token in ops_dict:
            if operators:
                # Check if the top operator is in the ops_dict and the precedence of it is greater than the current token
                while operators[-1] in ops_dict and \
                    ops_dict[operators[-1]] > ops_dict[token]:
                    postfix.append(operators.pop())
            operators.append(token)
        elif token == '(':
            operators.append(token)
        elif token == ')':
            while len(operators) > 0 and operators[-1] != "(":
                postfix.append(operators.pop())
            if len(operators) == 0:
                # Incomplete parenthesis, exit the program
                exit()
            if operators[-1] == "(":
                operators.pop()
        else:
            postfix.append(stemmer.stem(token.lower()))
    
    operators.reverse()
    postfix.extend(operators)
    return postfix
    

def split_string(query):
    tokens = []
    curr = ""

    for char in query:
        if char == '(' or char == ')':
            if curr:
                tokens.append(curr)
                curr = ""
            tokens.append(char)
        elif char == ' ':
            if curr:
                tokens.append(curr)
                curr = ""
        else:
            curr += char

    if curr:
        tokens.append(curr)

    return tokens

def process_query(tokens, term_dictionary, postings_file, doc_id_set):
    stack = []
    for token in tokens:
        if token not in ops_dict:
            # Regular string term
            stack.append(token)
        else:
            left_operand = posting_list_type_check(stack.pop(), term_dictionary, postings_file)
            operands = []
            intermediate_result = []
            if token == 'NOT':
                intermediate_result = posting_list_negation(doc_id_set, left_operand)
            elif token == 'AND':
                right_operand = posting_list_type_check(stack.pop(), term_dictionary, postings_file)
                operands = [left_operand, right_operand]
                intermediate_result = process_and_operator(operands)
            elif token == 'OR':
                right_operand = posting_list_type_check(stack.pop(), term_dictionary, postings_file)
                operands = [left_operand, right_operand]
                intermediate_result = process_or_operator(operands)
            stack.append(intermediate_result)
    if len(stack) > 0:
        query_result = stack.pop()
        if type(query_result) == str:
            query_result = get_postings_list(query_result, term_dictionary, postings_file)
        return query_result


def posting_list_type_check(operand, term_dictionary, postings_file):
    if type(operand) != list:
        operand = get_postings_list(operand, term_dictionary, postings_file)
    return operand

# Start of AND operation functions
def process_and_operator(operands):
    """
    Process AND operators and operands.

    If there is a NOT operator, then the NOT operator will be the last operand.
    """
    priority_queue = []

    for operand in operands:
        doc_frequency = len(operand)
        priority_queue.append((operand, doc_frequency))
    
    priority_queue.sort(key=lambda x: x[1])

    if priority_queue:
        prev_merged_list = priority_queue.pop(0)[0]
        while priority_queue:
            curr = priority_queue.pop(0)[0]
            prev_merged_list = intersect_merge_AND(prev_merged_list, curr)

    return prev_merged_list


def intersect_merge_AND(postings_list1, postings_list2):
    """
    Merge two postings lists using the intersect merge algorithm with skip pointers.
    """
    merged_postings_list = []
    p1 = p2 = 0
    if len(postings_list1) == 0 or len(postings_list2) == 0:
        return []
    else:
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
                    if p1 == len(postings_list1)-1:
                        p1 += 1
                    else:
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
                    if p2 == len(postings_list2)-1:
                        p2 += 1
                    else:
                        while isinstance(next_element, list) and next_element[0] <= list1_value:
                            p2 = list2_skip_ptr
                            if isinstance(postings_list2[list2_skip_ptr], list):
                                list2_skip_ptr = next_element[1]
                                next_element = postings_list2[list2_skip_ptr]
                else:
                    p2 += 1

    return merged_postings_list
# End of AND operation functions

# Start of OR operation functions
def process_or_operator(operands):
    """
        Process OR operators.

        If there is a NOT operator, then the NOT operator will be the last operand.
        """
    prev_postings_list = []
    while len(operands) > 0:
        if len(prev_postings_list) == 0:
            prev_postings_list = operands.pop()
            continue

        curr = operands.pop()
        prev_postings_list = union_merge(prev_postings_list, curr)

    return prev_postings_list

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

# End of OR operation functions

def get_postings_list_value(postings_list, ptr):
    left_comparator = 0
    if isinstance(postings_list[ptr], list):
        left_comparator = postings_list[ptr][0]
    else:
        left_comparator = postings_list[ptr]
    return left_comparator


# Start of NOT operation
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
    

def intersect_merge_NOT(postings_list1, postings_list2):
    """
    Merge two postings list, removing the postings in postings_list1 from postings_list2.
    """
    merged_postings_list = []
    postings_list1 = flatten(postings_list1)
    postings_list2 = flatten(postings_list2)
    if len(postings_list1) == 0:
        return postings_list1
    elif len(postings_list2) == 0:
        return postings_list2
    else:
        pl1 = set(postings_list1)
        pl2 = set(postings_list2)
        merged_postings_list = [term for term in pl1 if term not in pl2]
        return merged_postings_list

# End of NOT Operation

def flatten(posting_list):
    postings_list_build = []
    for term in posting_list:
        if isinstance(term, list):
            term = term[0]
        postings_list_build.append(term)
    return postings_list_build
        

def get_postings_list(term, term_dictionary, postings_file, temp_dict = None):
    if temp_dict and term[0] == "*":
        return temp_dict.get(term[1:])

    if term not in term_dictionary:
        return []
    
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

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None:
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)