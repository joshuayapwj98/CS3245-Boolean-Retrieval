#!/usr/bin/python3
import re
from nltk.stem.porter import PorterStemmer
import sys
import getopt

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

ops_dict = {'OR': 0, 'AND': 1, 'NOT': 2, '(': 3, ')': 3}

doc_id_set = {}
stemmer = PorterStemmer()

def run_search(dict_file, postings_file, queries_file, results_file):
    """
    Performs searching on the given queries file and output the results to a file
    using the given dictionary file and postings file.
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

        # Iterate through each line of the dictionary (except the last line)
        for i in range(len(lines)):
            line = lines[i]
            term, doc_frequency, file_ptr_pos = line.split()
            term_dictionary[term] = (doc_frequency, file_ptr_pos)

    with open(f'{queries_file}', "r") as queries_file,\
            open(f'{postings_file}', 'r') as postings_file,\
            open(f'{results_file}', "w") as results_file:
        # Read the queries file as raw string
        doc_id_set = list(get_postings_list('all_dict', term_dictionary, postings_file))

        queries_text = queries_file.read()
        queries = queries_text.split('\n')

        # Process each query and write results to the results file
        for i, query in enumerate(queries):
            post_fix = get_postfix(query)
            query_results = process_query(post_fix, term_dictionary, postings_file, doc_id_set)
            string_builder = ''
            for id in query_results:
                if type(id) == list:
                    string_builder = ' '.join(str(i) for i in id)
                else:   
                    string_builder += str(id) + ' '
            string_builder = string_builder.rstrip()
            results_file.write(string_builder)
            if i < len(queries) - 1:
                results_file.write("\n")

def get_postfix(infix):
    """
    Converts an infix expression to Reverse Polish Notation using the Shunting Yard algorithm.
    """
    # Initialize stack and queue
    operators = []
    postfix = []
    global ops_dict

    # Split the infix expression into tokens
    tokens = split_string(infix)

    for token in tokens:
        if token in ops_dict:
            # Check if the top operator is in the ops_dict and the
            # precedence of it is greater than the current token
            while operators and operators[-1] in ops_dict and \
                  ops_dict[operators[-1]] > ops_dict[token]:
                # Append the operator into the postfix list
                # Pop the operator from the operators stack
                postfix.append(operators.pop())
            operators.append(token)
        elif token == '(':
            operators.append(token)
        elif token == ')':
            while operators[-1] != "(":
                postfix.append(operators.pop())
            operators.pop()
            if len(operators) == 0:
                # Incomplete parenthesis, exit the program
                exit()
        else:
            postfix.append(stemmer.stem(token.lower()))
    
    while operators:
        postfix.append(operators.pop())
    
    postfix = [token for token in postfix if token not in ['(', ')']]
    return postfix
    

def split_string(query):
    """
    Tokenizes a string by separating individual strings separated by spaces,
    opening and closing parentheses will appear as individual tokens.
    """
    tokens = []
    curr = ''

    for char in query:
        if char == '(' or char == ')':
            if curr:
                tokens.append(curr)
                curr = ''
            tokens.append(char)
        elif char == ' ':
            if curr:
                tokens.append(curr)
                curr = ''
        else:
            curr += char

    if curr:
        tokens.append(curr)

    return tokens

def process_query(tokens, term_dictionary, postings_file, doc_id_set):
    """
    Processes the boolean query and returns a postings lists.

    Queries are input as tokens in Reverse Polish Notation. A list of all documents
    ids is also taken as input to process negation operations.
    """
    stack = []
    for token in tokens:
        if token not in ops_dict:
            # Regular string term
            stack.append(token)
        else:
            # Pop the next term in the stack and retrieve the postings_list 
            left_operand = posting_list_type_check(stack.pop(), term_dictionary, postings_file)
            operands = []
            intermediate_result = []
            if token == 'NOT':
                # Perform negatation on the term
                # Returns a postings_list that contains elements not in left_operand
                intermediate_result = posting_list_negation(doc_id_set, left_operand)

            elif token == 'AND':
                # Pop the next term in the stack and retrieve the postings_list 
                right_operand = posting_list_type_check(stack.pop(), term_dictionary, postings_file)
                operands = [left_operand, right_operand]
                # Perform 'AND' operation on the operands and gets the postings_list
                intermediate_result = process_and_operator(operands)

            elif token == 'OR':
                # Perform 'OR' operation on the operands and gets the postings_list
                right_operand = posting_list_type_check(stack.pop(), term_dictionary, postings_file)
                operands = [left_operand, right_operand]
                intermediate_result = process_or_operator(operands)
            # Append the result to the stack
            stack.append(intermediate_result)
    if len(stack) > 0:
        query_result = stack.pop()
        # Edge case: If there is only 1 querable term, retrieve the individual postings_list and return
        if type(query_result) == str:
            query_result = get_postings_list(query_result, term_dictionary, postings_file)
        return query_result


def posting_list_type_check(operand, term_dictionary, postings_file):
    """
    Returns the postings_list of the operand if it is a string term.
    """
    if type(operand) != list:
        # Get the operand's postings_list
        operand = get_postings_list(operand, term_dictionary, postings_file)
    return operand

# ============== [START] AND OPERATIONS ==============
def process_and_operator(operands):
    """
    Processes AND operator and returns a postings_list.
    """
    return intersect_merge_AND(operands[0], operands[1])


def intersect_merge_AND(postings_list1, postings_list2):
    """
    Merges two postings lists using the intersect merge algorithm with skip pointers.
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
            if type(postings_list1[p1]) == list:
                list1_value, list1_skip_ptr = postings_list1[p1]
            else:
                list1_value = postings_list1[p1]

            # Check if the current element in postings_list2 contains a skip pointer
            if type(postings_list2[p2]) == list:
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
                    p1 = list1_skip_ptr
                    if p1 == len(postings_list1):
                        p1 += 1
                    else:
                        next_element = postings_list1[list1_skip_ptr]
                        # Continuously attempt to skip
                        while type(next_element) == list and next_element[0] <= list2_value:
                            p1 = list1_skip_ptr
                            if type(postings_list1[list1_skip_ptr]) == list:
                                # the next element is also contains a skip pointer
                                list1_skip_ptr = next_element[1]
                                next_element = postings_list1[list1_skip_ptr]
                            else:
                                break
                else:
                    p1 += 1

            # Case 3: list1_value >= list2_value
            else:
                if list2_skip_ptr != None and get_postings_list_value(postings_list2, list2_skip_ptr) <= list1_value:
                    p2 = list2_skip_ptr
                    if p2 == len(postings_list2):
                        p2 += 1
                    else:
                        next_element = postings_list2[list2_skip_ptr]
                        # Continuously attempt to skip
                        while type(next_element) == list and next_element[0] <= list1_value:
                            p2 = list2_skip_ptr
                            if type(postings_list2[list2_skip_ptr]) == list:
                                # the next element is also contains a skip pointer
                                list2_skip_ptr = next_element[1]
                                next_element = postings_list2[list2_skip_ptr]
                            else:
                                break
                else:
                    p2 += 1

    return merged_postings_list

def get_postings_list_value(postings_list, ptr):
    """
    Returns value of the postings_list at the given pointer.
    """
    left_comparator = 0
    if type(postings_list[ptr]) == list:
        left_comparator = postings_list[ptr][0]
    else:
        left_comparator = postings_list[ptr]
    return left_comparator
# ============== [END] AND OPERATIONS ==============




# ============== [START] OR OPERATIONS ==============
def process_or_operator(operands):
    """
    Processes OR operator and returns a postings_list.
    """
    return union_merge(operands[0], operands[1])

def union_merge(postings_list1, postings_list2):
    """
    Merges two postings lists using the union merge algorithm.
    """
    merged_postings_list = []
    p1 = p2 = 0

    while p1 < len(postings_list1) and p2 < len(postings_list2):
        list1_value = None
        list2_value = None

        if type(postings_list1[p1]) == list:
            list1_value, _ = postings_list1[p1]
        else:
            list1_value = postings_list1[p1]

        if type(postings_list2[p2]) == list:
            list2_value, _ = postings_list2[p2]
        else:
            list2_value = postings_list2[p2]

        if list1_value == list2_value:
            # Found a match
            # Append the result and increment both pointers
            merged_postings_list.append(list1_value)
            p1 += 1
            p2 += 1
        # Append the smaller value and increment its pointer
        elif list1_value < list2_value:
            merged_postings_list.append(list1_value)
            p1 += 1
        else:
            merged_postings_list.append(list2_value)
            p2 += 1

    # If any of the list contains elements but has yet to merge, extend the remaining into merged_postings_list
    if p1 < len(postings_list1) and p2 >= len(postings_list2):
        merged_postings_list.extend(postings_list1[p1:])

    if p2 < len(postings_list2) and p1 >= len(postings_list1):
        merged_postings_list.extend(postings_list2[p2:])

    return merged_postings_list
# ============== [END] OR OPERATIONS ==============


# ============== [START] NOT OPERATIONS ==============
def posting_list_negation(posting_list_all, posting_list1):
    """
    Returns the negated postings list.
    """
    result = []
    p1 = p_all = 0

    while p_all < len(posting_list_all):
        if p1 >= len(posting_list1):
            result.extend(posting_list_all[p_all:])
            break

        list1_value = None

        if type(posting_list1[p1]) == list:
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
    Merges two postings list, removing the postings in postings_list2 from postings_list1.
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

def flatten(posting_list):
    """
    Flattens a postings list by removing skip pointers.
    """
    postings_list_build = []
    for term in posting_list:
        if type(term) == list:
            term = term[0]
        postings_list_build.append(term)
    return postings_list_build
# ============== [END] NOT OPERATIONS ==============
        

def get_postings_list(term, term_dictionary, postings_file):
    """
    Returns the postings list for the given term.
    """
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