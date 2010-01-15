import math
import random
import struct
import sys

epsilon = 0.01
q = 3
aux_seed = 23
f = int(math.ceil(math.log(epsilon**2/4.0)/math.log(1.0 - epsilon/2.0)))
rhos = [1.0 - ((1 + 1.0/f)/(1 + epsilon))]
for i in range(1, f):
    rhos.append(((1 - rhos[0])*f)/((f-1)*(i+1)*i))

id_flag = 'i'
id_size = struct.calcsize(id_flag)

assert math.fsum(rhos) == 1.0

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
    def __init__(self, data, block_size):
        self.rand = random.Random()
        self.current_block_id = 0
        self.block_size = block_size
        self.num_message_blocks = int(math.ceil(float(len(data))/block_size))

        # Create message blocks
        message_blocks = []
        for i in range(0, self.num_message_blocks):
            message_block = struct.pack('%ds' % block_size, data[i*block_size:])
            message_blocks.append(map(ord, message_block))

        # Generate auxiliary blocks
        self.rand.seed(aux_seed)
        num_aux = int(math.floor(0.55*q*epsilon*len(message_blocks)))
        aux_blocks = []
        for i in range(0, num_aux):
            aux_blocks.append(xor_blocks(fsample(self.rand, message_blocks, q)))

        # Composite blocks
        self.blocks = message_blocks + aux_blocks

        print "Message blocks: %d" % len(message_blocks)
        print "Aux blocks: %d" % len(aux_blocks)

    def _get_block(self, id):
        self.rand.seed(id)
        degree = choose_degree(self.rand)
        composite_blocks = fsample(self.rand, self.blocks, degree)
        check_data = ''.join(map(chr, xor_blocks(composite_blocks)))
        return struct.pack('%s%ds' % (id_flag, len(check_data)), id, check_data)

    def next_block(self):
        block = self._get_block(self.current_block_id)
        self.current_block_id += 1
        return block

class Decoder(object):
    """An implementation of Online Codes, for decoding"""

    def __init__(self, block_size, message_size):
        self.rand = random.Random()
        self.block_size = block_size
        self.message_size = message_size

        self.num_message_blocks = int(math.ceil(float(message_size)/block_size))
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
        (block_id, block_data) = struct.unpack('%s%ds' % (id_flag, self.block_size), block)
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

        data = ''
        for i in range(0, self.num_message_blocks):
            data += ''.join(map(chr, self.composite_blocks[i]))
        return ''.join(data[:self.message_size])

def main():
    contents = open(sys.argv[1], 'rb').read()
    block_size = 8

    encoder = Encoder(contents, block_size)
    num_blocks = encoder.num_message_blocks

    print 'Number of message blocks: %d' % num_blocks

    decoder = Decoder(block_size, len(contents))
    num_fetched = 0
    while num_fetched < num_blocks:
        decoder.process_block(encoder.next_block())
        num_fetched += 1

    while not decoder.have_all_message_blocks():
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
