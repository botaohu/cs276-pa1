import struct
import array 

def to_gaps(arr):
    return [arr[0]] + map(lambda p : p[1] - p[0], zip(arr[:-1], arr[1:]))
  
def from_gaps(arr):
  sum = 0
  res = []
  for gap in arr:
    sum += gap
    res.append(sum)
  return res

def vb_encode_num(num):
  bytes = array.array("B")
  while num >= 0x80:
    bytes.append(num & 0x7F)
    num >>= 7
  bytes.append(num) 
  bytes[0] |= 0x80; 
  bytes.reverse()
  return bytes
  
def vb_encode(arr):
  bytes = array.array("B")
  for num in arr:
    bytes.extend(vb_encode_num(num))
  return bytes
  
def vb_decode(bytes):
  arr = []
  sum = 0
  for byte in bytes:
    sum = (sum << 7) | (0x7F & byte);
    if byte & 0x80:
      arr.append(sum)  
      sum = 0  
  return arr

class BitArray:
  def __init__(self):
    self.cnt = 0
    self.bytes = array.array("B")
    
  def from_bytes(self, bytes):
    self.cnt = bytes * 8
    self.bytes = bytes
    
  def get_bit(self, index):
    return int(self.bytes[index >> 3] & (1 << (index & 0x7)) > 0)
     
  def append(self, bit):
    self.cnt += 1
    if (self.cnt >> 3) >= len(self.bytes):
      self.bytes.append(0)
    index = self.cnt - 1
    if bit:
      self.bytes[index >> 3] |= (1 << (index & 0x7))
  
  def to_bytes(self):
    return self.bytes

def gamma_encode(arr):
  bits = BitArray()
  for num in arr:
    n = num + 2  #all number + 2
    n1 = 0
    n2 = n
    while n2 > 0:
      n1 += 1
      n2 >>= 1
    for _ in xrange(n1 - 1):
      bits.append(1)
    bits.append(0)
    n2 = n
    for i in xrange(n1 - 2, -1, -1):
      bits.append(n2 & (1 << i))
  return bits.to_bytes()

def gamma_decode(bytes):
  bits = BitArray()
  bits.from_bytes(bytes)
  arr = []
  i = 0
  while i < bits.cnt:
    n1 = 0
    while bits.get_bit(i) == 1:
      n1 += 1
      i += 1
    i += 1
    sum = 1
    for j in xrange(n1):
      sum = (sum << 1) | bits.get_bit(i)
      i += 1
    if sum == 1:
      break
    sum -= 2
    arr.append(sum)
  return arr

class Corpus:
  def print_posting(self, f, posting):
    pass
  def read_posting(self, f):
    pass

class BasicCorpus(Corpus):
  def print_posting(self, f, posting):
    term_id, docs_id = posting
    encoded_docs_id = array.array("I", docs_id)
    f.write(struct.pack("II", term_id, len(encoded_docs_id)))
    encoded_docs_id.tofile(f)
    
  def read_posting(self, f):
    buf = f.read(struct.calcsize("II"))
    if len(buf) > 0:
      term_id, length = struct.unpack("II", buf)
      encoded_docs_id = array.array("I")
      encoded_docs_id.fromfile(f, length)
      return term_id, encoded_docs_id.tolist()
    
class CompressedCorpus(Corpus):
  def print_posting(self, f, posting):
    term_id, docs_id = posting
    encoded_docs_id = vb_encode(to_gaps(docs_id))
    f.write(struct.pack("II", term_id, len(encoded_docs_id)))
    encoded_docs_id.tofile(f)
    
  def read_posting(self, f):
    buf = f.read(struct.calcsize("II"))
    if len(buf) > 0:
      term_id, length = struct.unpack("II", buf)
      encoded_docs_id = array.array("B")
      encoded_docs_id.fromfile(f, length)
      return term_id, from_gaps(vb_decode(encoded_docs_id.tolist()))

class GammaCompressedCorpus(Corpus):
  def print_posting(self, f, posting):
    term_id, docs_id = posting
    encoded_docs_id = gamma_encode(to_gaps(docs_id))
    f.write(struct.pack("II", term_id, len(encoded_docs_id)))
    encoded_docs_id.tofile(f)
    
  def read_posting(self, f):
    buf = f.read(struct.calcsize("II"))
    if len(buf) > 0:
      term_id, length = struct.unpack("II", buf)
      encoded_docs_id = array.array("B")
      encoded_docs_id.fromfile(f, length)
      return term_id, from_gaps(gamma_decode(encoded_docs_id))
  
