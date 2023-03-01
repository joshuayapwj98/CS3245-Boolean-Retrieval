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


def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')

    with open(f'{queries_file}.txt', "r") as queries_file, open(f'{results_file}.txt', "w") as results_file,\
            open(f'{dict_file}', 'r') as dictionary_file, open(f'{postings_file}', 'r') as postings_file:

        term_dictionary = {}

        for line in dictionary_file:
            term, doc_frequency, file_ptr_pos = line.split()
            term_dictionary[term] = (doc_frequency, file_ptr_pos)

        queries = queries_file.readlines()

        for query in queries:
            query_results = process_query(query, term_dictionary, postings_file)
            results_file.write(f'{query_results}\n')

def process_query(query, term_dictionary, postings_file):
    """
    For each query, process the query and return the results (posting list)
    """
    assert len(query) <= 1024, "Query must be under 1024 characters."

    # tokenize the query
    split_query = query.split()

    # perform stemming
    split_query_stemmed = [stemmer.stem(token.lower())
                           for token in split_query if token not in OPERANDS_LIST]

    split_query_without_parenthesis = []
    i = 0
    open_parenthesis_index = 0
    while i < len(split_query_stemmed):
        # check for expressions in parentheses, and evaluate them
        if split_query_stemmed[i] == "(":
            open_parenthesis_index = i
            i += 1
            continue
        if split_query_stemmed[i] == ")":
            expression = split_query_stemmed[open_parenthesis_index:i + 1]
            assert "(" not in expression, "no nested parenthesis."
            processed_expression = process_query_no_parenthesis(expression, term_dictionary, postings_file)
            split_query_without_parenthesis.append(processed_expression)
            i += 1
            continue

        # group "NOT" and the next word together (e.g. "NOT", "apple" -> ["NOT", "apple"])
        if split_query_stemmed[i] == "NOT":
            split_query_without_parenthesis.append(split_query_stemmed[i:i + 2])
            i += 2
            continue

        # for all other cases, just add the word to the list
        split_query_without_parenthesis.append(split_query_stemmed[i])
        i += 1

def process_or_operator(operands, term_dictionary, postings_file):
    assert len(operands) > 0, "OR operator must have at least one operand."

    temp_results = get_postings_list(operands[0])

    # TODO : OR merging for operands with NOT operator

    index = 1;
    while index < len(operands):
        curr_operand = operands[index]


    return temp_results

def union_merge(postings_list1, postings_list2):
    merged_postings_list = []
    p1 = p2 = 0


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
        curr = pq.get()
        posting_list_curr = get_postings_list(curr, term_dictionary, postings_file)
        temp_results = intersect_merge(temp_results, posting_list_curr)

    while len(not_operands) > 0:
            curr = not_operands.pop()
            posting_list_curr = get_postings_list(curr, term_dictionary, postings_file)
            temp_results = intersect_merge_NOT(temp_results, posting_list_curr)

    return temp_results

def intersect_merge(postings_list1, postings_list2):
    """
    Merge two postings lists using the intersect merge algorithm with skip pointers.
    """
    merged_postings_list = []
    p1 = p2 = 0

    while p1 < len(postings_list1) and p2 < len(postings_list2):
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
            merged_postings_list.append(list1_value)
            p1 += 1
            p2 += 1

        # Case 2: list1_value < list2_value
        elif list1_value < list2_value:
            if list1_skip_ptr and postings_list1[list1_skip_ptr] <= list2_value:
                while isinstance(postings_list1[p1], list) and postings_list1[postings_list1[p1][1]][0] <= list2_value:
                    p1 = postings_list1[postings_list1[p1][1]]
            else:
                p1 += 1

        # Case 3: list1_value >= list2_value
        elif list2_skip_ptr and postings_list2[list2_skip_ptr] <= list1_value:
            if list2_skip_ptr and postings_list1[list1_skip_ptr] <= list1_value:
                while isinstance(postings_list2[p2], list) and postings_list2[postings_list2[p2][0]] <= list1_value:
                    p2 = postings_list2[postings_list2[p2][1]]
            else:
                p2 += 1

    return merged_postings_list

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

# class LinkedListNode:
#
#     toString = this.node + nextnode.tostring()



def process_query_no_parenthesis(query_list, term_dictionary, postings_file):
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
            temp_results.append(process_and_operator(AND_operands, term_dictionary, postings_file))
            i = i + 2 * k
            continue

        temp_results.append(query_list[i])
        i += 1

    OR_operands = [i for i in temp_results if i != "OR"]
    return process_or_operator(OR_operands, term_dictionary, postings_file)


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
    print(term)
    print(postings_list)
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

# run_search(dictionary_file, postings_file, file_of_queries, file_of_output)


with open('dictionary.txt', 'r') as dictionary_file, open('postings.txt', 'r') as postings_file:

    term_dictionary = {}

    for line in dictionary_file:
        term, doc_frequency, file_ptr_pos = line.split()
        term_dictionary[term] = (doc_frequency, file_ptr_pos)

    operands = ['-0.6', '-0.6']

    print(process_and_operator(operands, term_dictionary, postings_file))

    # met[[200, 10], 296, 835, 1000, 1535, 1772, 1777, 1860, 1920, 1996, [2095,
    #                                                                     20], 2121, 2195, 2246, 2251, 2286, 2802, 2924, 2948, 2996, [
    #     3356, 30], 3452, 3594, 3916, 3982, 4043, 4303, 4625, 5156, 5178, [5193,
    #                                                                       40], 5212, 5258, 5278, 5304, 5330, 5382, 5711, 6116, 6127, [
    #     6128, 50], 6137, 6442, 6712, 6926, 7130, 7196, 7326, 7356, 7559, [7628,
    #                                                                       60], 7765, 7796, 7950, 8044, 8080, 8103, 8109, 8184, 8188, [
    #     8198, 70], 8518, 8606, 9069, 9164, 9336, 9637, 9733, 9751, 9793, [9897,
    #                                                                       80], 10192, 10213, 10306, 10339, 10452, 10563, 10674, 10689, 10752, [
    #     10771, 90], 10904, 11352, 12011, 12152, 12340, 12355, 12443, 12449, 12728, [12741,
    #                                                                                 94], 12815, 12846, 12965, 14757]
    #
    # meet[[9,
    #       26], 40, 42, 45, 110, 144, 146, 176, 203, 209, 227, 232, 236, 242, 248, 249, 256, 290, 303, 309, 322, 342, 345, 349, 353, 362, [
    #     369,
    #     52], 381, 393, 401, 402, 442, 443, 518, 525, 551, 562, 677, 684, 714, 730, 754, 842, 857, 873, 875, 926, 937, 942, 952, 969, 991, [
    #     1000,
    #     78], 1074, 1103, 1110, 1148, 1207, 1212, 1213, 1292, 1306, 1312, 1316, 1526, 1533, 1535, 1562, 1601, 1622, 1675, 1692, 1696, 1718, 1729, 1739, 1771, 1836, [
    #     1845,
    #     104], 1848, 1855, 1862, 1889, 1909, 1920, 1963, 1967, 1971, 1994, 2013, 2064, 2087, 2095, 2121, 2159, 2197, 2251, 2259, 2268, 2278, 2352, 2357, 2359, 2367, [
    #     2376,
    #     130], 2383, 2417, 2425, 2508, 2550, 2553, 2638, 2652, 2686, 2697, 2709, 2725, 2747, 2764, 2777, 2791, 2857, 2948, 2952, 2971, 2973, 3019, 3020, 3023, 3028, [
    #     3031,
    #     156], 3034, 3048, 3051, 3062, 3065, 3084, 3117, 3191, 3194, 3216, 3246, 3292, 3344, 3352, 3390, 3394, 3399, 3421, 3435, 3441, 3445, 3452, 3459, 3473, 3493, [
    #     3512,
    #     182], 3514, 3542, 3553, 3556, 3571, 3572, 3575, 3578, 3587, 3594, 3609, 3645, 3748, 3779, 3800, 3838, 3868, 3869, 3881, 3892, 3906, 3916, 3928, 3961, 4026, [
    #     4027,
    #     208], 4028, 4043, 4071, 4156, 4175, 4267, 4277, 4349, 4405, 4429, 4490, 4524, 4548, 4551, 4577, 4583, 4603, 4609, 4625, 4630, 4662, 4664, 4713, 4714, 4735, [
    #     4781,
    #     234], 4798, 4806, 4809, 4824, 4867, 4941, 4953, 4964, 4976, 4983, 5042, 5071, 5092, 5118, 5139, 5167, 5168, 5171, 5172, 5175, 5176, 5177, 5192, 5193, 5214, [
    #     5234,
    #     260], 5258, 5268, 5273, 5285, 5286, 5290, 5291, 5303, 5335, 5351, 5352, 5382, 5390, 5391, 5394, 5445, 5455, 5471, 5499, 5511, 5570, 5585, 5598, 5660, 5667, [
    #     5702,
    #     286], 5711, 5734, 5746, 5752, 5778, 5786, 5812, 5833, 5858, 5880, 5895, 5954, 5973, 6062, 6075, 6108, 6127, 6128, 6137, 6153, 6265, 6267, 6269, 6326, 6340, [
    #     6346,
    #     312], 6352, 6414, 6426, 6434, 6438, 6463, 6499, 6576, 6595, 6632, 6635, 6636, 6657, 6707, 6720, 6726, 6732, 6740, 6742, 6744, 6815, 6846, 6863, 6877, 6882, [
    #     6912,
    #     338], 6926, 6941, 7011, 7031, 7037, 7041, 7060, 7062, 7071, 7088, 7097, 7103, 7124, 7135, 7161, 7185, 7217, 7263, 7311, 7313, 7319, 7323, 7326, 7336, 7356, [
    #     7382,
    #     364], 7391, 7406, 7512, 7533, 7558, 7566, 7592, 7625, 7628, 7632, 7643, 7659, 7670, 7785, 7792, 7796, 7802, 7816, 7864, 7873, 7875, 7876, 7888, 7891, 7903, [
    #     7940,
    #     390], 7950, 7972, 8029, 8040, 8044, 8055, 8069, 8074, 8080, 8087, 8097, 8102, 8105, 8106, 8115, 8130, 8135, 8137, 8141, 8151, 8156, 8186, 8189, 8198, 8204, [
    #     8210,
    #     416], 8214, 8240, 8244, 8252, 8309, 8322, 8342, 8421, 8510, 8541, 8562, 8578, 8592, 8596, 8598, 8602, 8608, 8630, 8635, 8637, 8662, 8663, 8667, 8675, 8676, [
    #     8688,
    #     442], 8722, 8747, 8765, 8796, 8895, 8922, 8943, 8961, 8991, 9015, 9036, 9048, 9051, 9064, 9087, 9138, 9170, 9172, 9216, 9348, 9363, 9371, 9403, 9413, 9436, [
    #     9450,
    #     468], 9532, 9544, 9559, 9560, 9592, 9604, 9618, 9628, 9638, 9654, 9657, 9674, 9680, 9705, 9706, 9707, 9720, 9754, 9760, 9764, 9822, 9833, 9871, 9891, 9927, [
    #     9940,
    #     494], 9946, 9959, 10002, 10015, 10067, 10081, 10091, 10100, 10122, 10124, 10171, 10192, 10208, 10228, 10230, 10246, 10268, 10280, 10282, 10342, 10382, 10395, 10398, 10403, 10445, [
    #     10449,
    #     520], 10452, 10505, 10509, 10537, 10539, 10545, 10555, 10563, 10586, 10588, 10617, 10623, 10633, 10636, 10638, 10640, 10676, 10696, 10743, 10760, 10767, 10780, 10782, 10784, 10804, [
    #     10807,
    #     546], 10822, 10830, 10876, 10895, 10902, 10903, 10944, 10959, 11000, 11007, 11015, 11025, 11063, 11076, 11105, 11118, 11149, 11181, 11183, 11198, 11209, 11222, 11224, 11225, 11234, [
    #     11254,
    #     572], 11260, 11265, 11281, 11297, 11299, 11322, 11359, 11372, 11397, 11428, 11430, 11437, 11451, 11464, 11492, 11497, 11506, 11536, 11541, 11558, 11580, 11661, 11734, 11746, 11763, [
    #     11817,
    #     598], 11820, 11829, 11841, 11848, 11861, 11866, 11900, 11918, 11981, 11984, 12011, 12044, 12059, 12073, 12121, 12146, 12152, 12156, 12178, 12209, 12216, 12281, 12317, 12337, 12338, [
    #     12404,
    #     624], 12420, 12443, 12447, 12456, 12461, 12465, 12471, 12490, 12574, 12737, 12770, 12774, 12780, 12788, 12791, 12806, 12815, 12827, 12842, 12848, 12965, 12969, 13039, 13046, 13053, [
    #     13136,
    #     650], 13157, 13210, 13243, 13244, 13251, 13261, 13263, 13270, 13271, 13531, 13532, 13649, 13869, 13904, 13908, 13958, 14126, 14199, 14220, 14263, 14293, 14434, 14539, 14629, 14739, [
    #     14757, 653], 14767, 14770, 14818]
