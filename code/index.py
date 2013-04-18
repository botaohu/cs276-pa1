#!/bin/env python
from collections import deque
import os, glob, os.path
import sys
from itertools import groupby
import re
from corpus import *

if len(sys.argv) != 4:
  print >> sys.stderr, 'usage: python index.py [Basic|VB|Gamma] data_dir output_dir' 
  os._exit(-1)

total_file_count = 0

if sys.argv[1] == "Basic":
  corpus = BasicCorpus()
elif sys.argv[1] == "VB":
  corpus = CompressedCorpus()
elif sys.argv[1] == "Gamma":
  corpus = GammaCompressedCorpus()
else:
  print >> sys.stderr, 'Index method must be "Basic", "VB", or "Gamma"' 
  os._exit(-1)

root = sys.argv[2]
out_dir = sys.argv[3]
if not os.path.exists(out_dir):
  os.makedirs(out_dir)

# this is the actual posting lists dictionary
# word id -> {position_in_file, doc freq}
posting_dict = {}
# this is a dict holding document name -> doc_id
doc_id_dict = {}
# this is a dict holding word -> word_id
word_dict = {}
# this is a queue holding block names, later used for merging blocks
block_q = deque([])

# function to count number of files in collection
def count_file():
  global total_file_count
  total_file_count += 1

# pop out postings
def popLeftOrNone(posting_deque):
  if len(posting_deque) > 0:
    doc_id = posting_deque.popleft()
  else:
    doc_id = None
  return doc_id

# function for merging two lines of postings list to create a new line of merged results
def merge_posting(posting1, posting2):
  # don't forget to return the resulting line at the end
  word_id1, doc_list1 = p1
  word_id2, doc_list2 = p2
  assert(word_id1 == word_id2)
  doc_list1 = deque(doc_list1)
  doc_list2 = deque(doc_list2)
  doc_list = []
  pp1 = popLeftOrNone(doc_list1)
  pp2 = popLeftOrNone(doc_list2)
  while pp1 is not None and pp2 is not None:
    if pp1 == pp2:
      doc_list.append(pp1)
      pp1 = popLeftOrNone(doc_list1)
      pp2 = popLeftOrNone(doc_list2)
    elif pp1 < pp2:
      doc_list.append(pp1)
      pp1 = popLeftOrNone(doc_list1)
    else:
      doc_list.append(pp2)
      pp2 = popLeftOrNone(doc_list2)
  while pp1 is not None:
    doc_list.append(pp1)
    pp1 = popLeftOrNone(doc_list1)
  while pp2 is not None:
    doc_list.append(pp2)
    pp2 = popLeftOrNone(doc_list2)
  return (word_id1, doc_list)

# function for printing a line in a postings list to a given file
def print_posting(file, posting):
  # a useful function is f.tell(), which gives you the offset from beginning of file
  # you may also want to consider storing the file position and doc frequence in posting_dict in this call
  global posting_dict
  global corpus
  word_id, doc_list = posting
  posting_dict[word_id] = (file.tell(), len(doc_list))
  corpus.print_posting(file, posting)
#  print >> sys.stderr, word_id, " ", posting_dict[word_id], " ", doc_list

doc_id = -1
word_id = 0

for dir in sorted(os.listdir(root)):
  print >> sys.stderr, 'processing dir: ' + dir
  dir_name = os.path.join(root, dir)
  block_pl_name = out_dir+'/'+dir 
  # append block names to a queue, later used in merging
  block_q.append(dir)
  block_pl = open(block_pl_name, 'w')
  term_doc_list = []
  for f in sorted(os.listdir(dir_name)):
    count_file()
    file_id = os.path.join(dir, f)
    doc_id += 1
    doc_id_dict[file_id] = doc_id
    fullpath = os.path.join(dir_name, f)
    file = open(fullpath, 'r')
    for line in file.readlines():
      tokens = line.strip().split()
      for token in tokens:
        if token not in word_dict:
          word_dict[token] = word_id
          word_id += 1
        term_doc_list.append( (word_dict[token], doc_id) )
  # sort term doc list
  term_doc_list = sorted(set(term_doc_list))
  # write the posting lists to block_pl for this current block 
  groups = groupby(term_doc_list, key = lambda x : x[0])
  
  for word_id, term_doc_list in groups:
    print_posting(block_pl, (word_id, [doc for word_id, doc in term_doc_list]))
  
  block_pl.close()

print >> sys.stderr, '######\nposting list construction finished!\n##########'

print >> sys.stderr, '\nMerging postings...'
while True:
  if len(block_q) <= 1:
    break
  b1 = block_q.popleft()
  b2 = block_q.popleft()
  print >> sys.stderr, 'merging %s and %s' % (b1, b2)
  b1_f = open(out_dir+'/'+b1, 'r')
  b2_f = open(out_dir+'/'+b2, 'r')
  comb = b1+'+'+b2
  comb_f = open(out_dir + '/'+comb, 'w')
  
  # write the new merged posting lists block to file 'comb_f'
  p1 = corpus.read_posting(b1_f)
  p2 = corpus.read_posting(b2_f)
  while p1 or p2:
    if not p1 or not p2:
      p = p1 or p2
      print_posting(comb_f, p)
      p1 = corpus.read_posting(b1_f)
      p2 = corpus.read_posting(b2_f)
    else:  
      t1 = p1[0]
      t2 = p2[0]
      if t1 == t2:
        p = merge_posting(p1, p2)
        print_posting(comb_f, p)
        p1 = corpus.read_posting(b1_f)
        p2 = corpus.read_posting(b2_f)
      elif t1 < t2:
        print_posting(comb_f, p1)
        p1 = corpus.read_posting(b1_f)
      else:
        print_posting(comb_f, p2)
        p2 = corpus.read_posting(b2_f)
        
  b1_f.close()
  b2_f.close()
  comb_f.close()
  os.remove(out_dir+'/'+b1)
  os.remove(out_dir+'/'+b2)
  block_q.append(comb)
    
print >> sys.stderr, '\nPosting Lists Merging DONE!'

# rename the final merged block to corpus.index
final_name = block_q.popleft()
os.rename(out_dir+'/'+final_name, out_dir+'/corpus.index')

# print all the dictionary files
doc_dict_f = open(out_dir + '/doc.dict', 'w')
word_dict_f = open(out_dir + '/word.dict', 'w')
posting_dict_f = open(out_dir + '/posting.dict', 'w')
print >> doc_dict_f, '\n'.join( ['%s\t%d' % (k,v) for (k,v) in sorted(doc_id_dict.iteritems(), key=lambda(k,v):v)])
print >> word_dict_f, '\n'.join( ['%s\t%d' % (k,v) for (k,v) in sorted(word_dict.iteritems(), key=lambda(k,v):v)])
print >> posting_dict_f, '\n'.join(['%s\t%s' % (k,'\t'.join([str(elm) for elm in v])) for (k,v) in sorted(posting_dict.iteritems(), key=lambda(k,v):v)])
doc_dict_f.close()
word_dict_f.close()
posting_dict_f.close()

print total_file_count
