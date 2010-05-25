import math
import random
import struct
import sys
import numpy as np

import pdb

epsilon = 0.01
q = 3
aux_seed = 23
f = int(math.ceil(math.log(epsilon**2/4.0)/math.log(1.0 - epsilon/2.0)))
rhos = [1.0 - ((1 + 1.0/f)/(1 + epsilon))]
for i in range(1, f):
    rhos.append(((1 - rhos[0])*f)/((f-1)*(i+1)*i))

assert math.fsum(rhos) == 1.0

id_flag = 'i'
id_size = struct.calcsize(id_flag)

def choose_degree(rand):
    sample = rand.random()
    total = 0.0

    for i in range(0, len(rhos)):
        if sample < total + rhos[i]:
            return i+1
        total += rhos[i]

def block_xor(a, b):
    if len(a) != len(b):
        raise ValueError
    else:
        return map(lambda (a, b): a ^ b, zip(a, b))

def xor_blocks(blocks):
    return reduce(block_xor, blocks)

def fsample(rand, l, n):
    if len(l) < n:
        return l
    else:
        return rand.sample(l, n)

class Encoder(object):
    def __init__(self, data, block_size, id_bytes):
        self.rand = random.Random()
        self.current_block_id = 0
        self.block_size = block_size - id_bytes
        if id_bytes == 1:
            self.id_flag = 'B'
        elif id_bytes == 2:
            self.id_flag = 'H'
        elif id_bytes == 4:
            self.id_flag = 'I'
        self.max_block_id = 2**(id_bytes*8)

        self.num_message_blocks = int(math.ceil(float(len(data))/self.block_size))

        # Create message blocks
        buffer = struct.pack('%ds' % (self.block_size*self.num_message_blocks), data)
        buffer_array = np.frombuffer(buffer, dtype='B1')
        message_blocks = buffer_array.reshape((self.num_message_blocks, self.block_size))

        # Generate auxiliary blocks
        self.rand.seed(aux_seed)
        self.num_aux_blocks = int(math.floor(0.55*q*epsilon*self.num_message_blocks))
        aux_blocks = np.ndarray((self.num_aux_blocks, self.block_size), dtype='B1')
        for i in range(self.num_aux_blocks):
            indices = fsample(self.rand, range(0, self.num_message_blocks), q)
            aux_blocks[i] = np.bitwise_xor.reduce(message_blocks.take(indices, axis=0))

        # Composite blocks
        self.blocks = np.append(message_blocks, aux_blocks, axis=0)
        self.num_blocks = self.num_message_blocks + self.num_aux_blocks

        #print "Message blocks: %d" % self.num_message_blocks
        #print "Aux blocks: %d" % self.num_aux_blocks

    def _get_block(self, id):
        self.rand.seed(id)
        degree = choose_degree(self.rand)
        indices = fsample(self.rand, range(self.num_blocks), degree)
        composite_blocks = self.blocks.take(indices, axis=0)
        check_block = np.bitwise_xor.reduce(composite_blocks, axis=0).tostring()
        return struct.pack('%s%ds' % (self.id_flag, len(check_block)), id, check_block)

    def next_block(self):
        block = self._get_block(self.current_block_id)
        self.current_block_id = (self.current_block_id + 1) % self.max_block_id
        return block

class Decoder(object):
    """An implementation of Online Codes, for decoding"""

    def __init__(self, block_size, id_bytes, message_size):
        self.rand = random.Random()
        self.block_size = block_size - id_bytes
        self.message_size = message_size

        if id_bytes == 1:
            self.id_flag = 'B'
        elif id_bytes == 2:
            self.id_flag = 'H'
        elif id_bytes == 4:
            self.id_flag = 'I'

        self.num_message_blocks = int(math.ceil(float(message_size)/self.block_size))
        self.num_composite_blocks = int(math.floor(0.55*q*epsilon*self.num_message_blocks)) + self.num_message_blocks

        self.composite_blocks = {}
        self.check_blocks = {}
        self.composite_adjacent = {}
        self.check_adjacent = {}

        possible_message_blocks = range(0, self.num_message_blocks)
        for i in range(0, self.num_message_blocks):
            self.composite_adjacent[i] = []
        self.rand.seed(aux_seed)
        for i in range(self.num_message_blocks, self.num_composite_blocks):
            self.composite_adjacent[i] = fsample(self.rand, possible_message_blocks, q)
        self.composite_indices = range(0, self.num_composite_blocks)

    def have_all_message_blocks(self):
        for i in range(0, self.num_message_blocks):
            if i not in self.composite_blocks:
                return False
        return True

    def process_block(self, block):
        (block_id, block_data) = struct.unpack('%s%ds' % (self.id_flag, self.block_size), block)
        block_data = map(ord, block_data)

        self.rand.seed(block_id)
        degree = choose_degree(self.rand)
        adj = fsample(self.rand, self.composite_indices, degree)
    
        needed = False
        for b in adj:
            if b not in self.composite_blocks:
                needed = True

        if needed:
            self.check_adjacent[block_id] = adj
            self.check_blocks[block_id] = block_data

        return needed

    def uncover_blocks(self, coded_blocks, coded_adjacent, src_blocks):
        discovered_block = True
        while discovered_block:
            discovered_block = False

            for i in coded_blocks:
                cb = coded_blocks[i]
                adj = coded_adjacent[i]

                num_unknown = 0
                for b in adj:
                    if b not in src_blocks:
                        num_unknown += 1

                if num_unknown == 1:
                    discovered_block = True
                    to_xor = [cb]

                    for b in adj:
                        if b in src_blocks:
                            to_xor.append(src_blocks[b])
                        else:
                            to_find = b

                    src_blocks[to_find] = xor_blocks(to_xor)
                    break

    def status(self):
        """print "Check: %s" % repr(self.check_blocks)
        print "Adjacent: %s" % repr(self.check_adjacent)
        print "CompAdjacent: %s" % repr(self.composite_adjacent)
        print "Composite: %s" % repr(self.composite_blocks)"""
        self.uncover_blocks(self.check_blocks, self.check_adjacent, self.composite_blocks)
        self.uncover_blocks(self.composite_blocks, self.composite_adjacent, self.composite_blocks)

        known_message_blocks = 0
        for i in range(0, self.num_message_blocks):
            if i in self.composite_blocks:
                known_message_blocks += 1

        return known_message_blocks

    def message_data(self):
        if self.status() != self.num_message_blocks:
            raise ValueError

        pdb.set_trace()

        data = ''
        for i in range(0, self.num_message_blocks):
            data += ''.join(map(chr, self.composite_blocks[i]))
        return ''.join(data[:self.message_size])

def main():
    contents = open(sys.argv[1], 'rb').read()
    to_fetch = int(sys.argv[2])
    block_size = 8

    encoder = Encoder(contents, block_size, 2)
    num_blocks = encoder.num_blocks

    print 'Number of message blocks: %d' % num_blocks

    blocks = []
    for i in range(to_fetch):
        blocks.append(encoder.next_block())

    random.shuffle(blocks)

    decoder = Decoder(block_size, 2, len(contents))

    num_fetched = 0
    for block in blocks:
        num_fetched += 1
        if decoder.have_all_message_blocks():
            break
        decoder.process_block(block)
        decoder.status()

    #while num_fetched < num_blocks:
    #    decoder.process_block(encoder.next_block())
    #    num_fetched += 1

    while not decoder.have_all_message_blocks():
        print 'Hello'
        for i in range(0, 100):
            encoder.next_block()
        decoder.process_block(encoder.next_block())
        num_fetched += 1

        decoder.status()

    decoded = decoder.message_data()

    num_mismatched = num_matched = 0

    for i in range(0, len(contents)):
        if contents[i] != decoded[i]:
            num_mismatched += 1
        else:
            num_matched += 1

    print 'Fetched %d check blocks' % num_fetched
    print '%d bytes do not match!' % num_mismatched
    print '%d bytes match' % num_matched

if __name__ == '__main__':
    main()
