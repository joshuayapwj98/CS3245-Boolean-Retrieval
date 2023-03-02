This is the README file for A0218297U and A0238889B's submission
Email(s): e0544333@u.nus.edu, e0773487@u.nus.edu

== Python Version ==

I'm (We're) using Python Version 3.8.15 for this assignment.

== General Notes about this assignment ==

Give an overview of your program, describe the important algorithms/steps 
in your program, and discuss your experiments in general.  A few paragraphs 
are usually sufficient.

The program indexes a list of supplied documents using SPIMI but with a fixed block size
and outputs a dictionary of the terms and a postings list file. We split the documents
into blocks of X documents, where X is a predefined block size of 2000. For each term in
each document in block, they are first stemmed using the Porter Stemmer algorithm
and converted to lower case. Then the terms are added to a dictionary,  where the key
is the term and value is list of documents ID. Since, we are processing documents in increasing
documents IDs, we know that the list of document ID will be monotonically increasing.
When the last document in the block is processed, the dictionary is sorted by the term and
written to a file.

Once all the blocks are processed, 2 way merge is performed to combine them. The dictionary
is stored in a text file with each line representing a term, its document frequency, and the
byte position of the postings list for that term in the postings list file. The postings list
file contains the document ids of the documents that contain the term, with skip pointers.

The program then allows the user to input a list of boolean queries to be processed
for their corresponding document ids.

Search uses shunting yard algorithm to convert the query to postfix notation,
and then evaluates the query using a stack. For intersection merge (i.e. AND operator),
we use a skip pointer as described in lecture  to optimise the merge.

== Files included with this submission ==

List the files in your submission here and provide a short 1 line
description of each file.  Make sure your submission's files are named
and formatted correctly.

1. README.txt - This file.

2. index.py - Code for indexing the documents in the corpus.

3. search.py - Code for processing boolean queries.

4. dictionary.txt - Dictionary of terms and their corresponding document frequencies and byte position in the postings list file.

5. postings.txt - Postings list file containing the document ids with skip pointers.

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[ X ] We, A0218297U and A0238889B, certify that I/we have followed the CS 3245 Information
Retrieval class guidelines for homework assignments.  In particular, I/we
expressly vow that I/we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  

[ ] I/We, A0000000X, did not follow the class rules regarding homework
assignment, because of the following reason:

<Please fill in>

We suggest that we should be graded as follows:

- Correctness of code
- Documentation in index.py, search.py, and in this README
- Evaluation results

<Please fill in>

== References ==

<Please list any websites and/or people you consulted with for this
assignment and state their role>
