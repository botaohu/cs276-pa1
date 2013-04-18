#!/bin/env python
from collections import deque
import os, glob, os.path
import sys
import re
from corpus import *

if len(sys.argv) != 3:
  print >> sys.stderr, 'usage: python query.py [Basic|VB|Gamma] index_dir' 
  os._exit(-1)

# pop out postings
def popLeftOrNone(posting_deque):
  if len(posting_deque) > 0:
    doc_id = posting_deque.popleft()
  else:
    doc_id = None
  return doc_id

def merge_posting (postings1, postings2):
  new_posting = []
  pp1 = popLeftOrNone(postings1);
  pp2 = popLeftOrNone(postings2);
  while pp1 is not None and pp2 is not None:
    if pp1 == pp2:
      new_posting.append(pp1)
      pp1 = popLeftOrNone(postings1)
      pp2 = popLeftOrNone(postings2)
    elif pp1 < pp2:
      pp1 = popLeftOrNone(postings1)
    else:
      pp2 = popLeftOrNone(postings2)
  return deque(new_posting)

# file locate of all the index related files

if sys.argv[1] == "Basic":
  corpus = BasicCorpus()
elif sys.argv[1] == "VB":
  corpus = CompressedCorpus()
elif sys.argv[1] == "Gamma":
  corpus = GammaCompressedCorpus()
else:
  print >> sys.stderr, 'Index method must be "Basic", "VB", or "Gamma"' 
  os._exit(-1)

index_dir = sys.argv[2]
index_f = open(index_dir+'/corpus.index', 'r')
word_dict_f = open(index_dir+'/word.dict', 'r')
doc_dict_f = open(index_dir+'/doc.dict', 'r')
posting_dict_f = open(index_dir+'/posting.dict', 'r')

word_dict = {}
doc_id_dict = {}
file_pos_dict = {}
doc_freq_dict = {}

print >> sys.stderr, 'loading word dict'
for line in word_dict_f.readlines():
  parts = line.split('\t')
  word_dict[parts[0]] = int(parts[1])
print >> sys.stderr, 'loading doc dict'
for line in doc_dict_f.readlines():
  parts = line.split('\t')
  doc_id_dict[int(parts[1])] = parts[0]
print >> sys.stderr, 'loading index'
for line in posting_dict_f.readlines():
  parts = line.split('\t')
  term_id = int(parts[0])
  file_pos = int(parts[1])
  doc_freq = int(parts[2])
  file_pos_dict[term_id] = file_pos
  doc_freq_dict[term_id] = doc_freq

def read_posting(term_id):
  # provide implementation for posting list lookup for a given term
  # a useful function to use is index_f.seek(file_pos), which does a disc seek to 
  # a position offset 'file_pos' from the beginning of the file
  global corpus
  index_f.seek(file_pos_dict[term_id])
  return deque(corpus.read_posting(index_f)[1])

#for i in range(0, 13):
#  print >> sys.stderr, i, " ", read_posting(i)
#for i in range(0, 5):
#  print >> sys.stderr, i, " ", doc_id_dict[i]

# read query from stdin
while True:
  input = sys.stdin.readline()
  input = input.strip()
  if len(input) == 0: # end of file reached
    break
  input_parts = input.split()

  query_term_ids = map(lambda w : word_dict[w] if w in word_dict else None, input_parts)
  if not all(map(lambda v : v is not None, query_term_ids)):
    print "no results found"
    continue
  query_term_ids = deque(sorted(query_term_ids, key = lambda t : doc_freq_dict[t], reverse=False))
  docs = read_posting(query_term_ids.popleft())
  while len(query_term_ids) > 0 and len(docs) > 0:
    new_docs = read_posting(query_term_ids.popleft())    
    docs = merge_posting(docs, new_docs)
  if len(docs) == 0:
    print "no results found"
  else:
    results = map(lambda d : doc_id_dict[d], docs)
    results.sort()
    for doc_name in results:
      print doc_name
      
