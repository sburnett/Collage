import hashlib
from Crypto.Cipher import AES
import bisect
import struct
import random
from math import log
import bz2

import coder
import snippets
import vectorlayer

import pdb

class MessageLayerError(Exception):
    pass

class MessageLayer(object):
    """Implementation of Collage's message layer. You must provide
    several parameters to this layer to use it in your application.
    
    Details not present in the paper:
    * Message sizes are powers of 2; This layer transparently handles extending
        messages to the next power of 2 if necessary, so application developers
        need not worry about this.
    * Erasure code block sizes are also powers of 2. The block size for a given
        message is derived from its length.
    * The message format is as follows: the message is padded with zeroes to the
        next power of two, including the padding header. The padding header contains
        the length of the padding appended to the message."""

    _int_bytes = struct.calcsize('I')
    _short_bytes = struct.calcsize('H')
    _char_bytes = struct.calcsize('B')
    _format_flags = {_int_bytes: 'I',
                    _short_bytes: 'H',
                    _char_bytes: 'B'}

    _header_compressed_mask = 0x80
    _header_padding_mask = 0x60
    _header_size_mask = 0x1F

    _size_bits = 5
    _padding_bits = 2
    _compressed_bits = 1

    _payload_multiple = AES.block_size

    # We have 2 bits in header to express padding, in terms of blocks
    _min_block_size = AES.block_size/4

    def __init__(self, vector_provider, block_size, block_id_bytes, snippet_dirs, task_mapping_size):
        """Initialize a message, using a particular Vector for storing message chunks."""

        if block_size < self._min_block_size:
            raise MessageLayerError('Block size too small')

        self._vector_provider = vector_provider
        self._block_size = block_size
        self._block_id_bytes = block_id_bytes

        self._task_mapping_size = task_mapping_size
        self._snippet_dirs = snippet_dirs
        self.reload_task_database()

    def reload_task_database(self):
        all_snippets = snippets.load_snippets(self._snippet_dirs)
        tasks = []
        for (send_snippet, receive_snippet, can_embed_snippet) in all_snippets.values():
            task = Task(send_snippet, receive_snippet, can_embed_snippet)
            tasks.append(task)
        self._task_database = TaskDatabase(tasks, self._task_mapping_size)

    def _sender_get_preamble_size(self, data_len):
        if data_len + self._char_bytes < (1 << self._char_bytes*8):
            return self._char_bytes
        elif data_len + self._short_bytes < (1 << self._short_bytes*8):
            return self._short_bytes
        elif data_len + self._int_bytes < (1 << self._int_bytes*8):
            return self._int_bytes
        else:
            raise ValueError('Message too big')

    def _format_message_data(self, data):
        """Pad a message with zeroes out to the nearest power of two, and store
            the length of the pad at the front of the message."""
        preamble_len = self._sender_get_preamble_size(len(data))
        format_flag = self._format_flags[preamble_len]
        data_len = len(data) + preamble_len
        real_len = 1
        while real_len < max(data_len, self._block_size):
            real_len <<= 1
        format_string = '%c%ds' % (format_flag, real_len - preamble_len)
        formatted_data = struct.pack(format_string, real_len - data_len, data)
        return formatted_data

    def _get_preamble_size(self, data_len):
        if data_len < (1 << self._char_bytes*8):
            return self._char_bytes
        elif data_len < (1 << self._short_bytes*8):
            return self._short_bytes
        elif data_len < (1 << self._int_bytes*8):
            return self._int_bytes
        else:
            raise ValueError('Message too big')

    def _prepare_payload(self, blocks, message_len):
        blocks_buf = ''.join(blocks)
        header = int(log(message_len, 2))

        compressed_blocks_buf = bz2.compress(blocks_buf)
        if len(blocks_buf) <= len(compressed_blocks_buf):
            buf_len = len(blocks_buf) + 1
            padding_len = self._payload_multiple - buf_len % self._payload_multiple
            padded_blocks = padding_len / self._block_size
            header = header | (padded_blocks << self._size_bits)
            payload = struct.pack('B%ds' % (buf_len + padding_len - 1,),
                                  header,
                                  blocks_buf)
        else:
            buf_len = len(compressed_blocks_buf) + 1
            buf_len += self._payload_multiple - buf_len % self._payload_multiple
            compressed_header = self._header_compressed_mask | header
            payload = struct.pack('B%ds' % (buf_len - 1,),
                                  compressed_header,
                                  compressed_blocks_buf)
        return payload

    def send(self, identifier, data, num_vectors):
        """Send a message with an associated identifier."""
    
        tasks = self._task_database.lookup(identifier)

        formatted_data = self._format_message_data(data)
        data_len = len(formatted_data)
        encoder = coder.Encoder(formatted_data, self._block_size, self._block_id_bytes)

        key = hashlib.sha1(identifier).digest()[:16]
        encrypter = AES.new(key)

        for i in range(num_vectors):
            vector_result = self._vector_provider.get_vector(tasks)
            if vector_result is None:
                raise MessageLayerError('Unable to acquire enough vectors')
            (cover_vector, task) = vector_result

            blocks_encoded = 1
            while True:
                blocks = []
                for j in range(blocks_encoded):
                    blocks.append(encoder.next_block())
                payload = self._prepare_payload(blocks, data_len)
                ciphertext = encrypter.encrypt(payload)
                try:
                    coded_vector = cover_vector.encode(ciphertext)
                except vectorlayer.EncodingError:
                    break
                else:
                    blocks_encoded <<= 1

            blocks_encoded >>= 1
            if blocks_encoded > 0:
                task.execute_send(coded_vector)
            else:
                self._vector_provider.repurpose_vector(vector)

    def _decode_data(self, data):
        preamble_len = self._get_preamble_size(len(data))
        preamble_flag = self._format_flags[preamble_len]
        (padding_len,) = struct.unpack(preamble_flag, data[:preamble_len])
        return data[preamble_len : len(data) - padding_len]

    def _get_blocks(self, payload):
        (header,) = struct.unpack('B', payload[0])
        blocks_buf = payload[1:]

        compressed = header & self._header_compressed_mask != 0
        padding = (header & self._header_padding_mask) >> self._size_bits
        message_len = 2**(header & self._header_size_mask)

        if compressed:
            blocks_buf = bz2.decompress(blocks_buf)
        else:
            payload_len = len(blocks_buf) - len(blocks_buf) % self._block_size
            payload_len -= padding*self._block_size
            blocks_buf = blocks_buf[:payload_len]

        blocks = []
        for idx in range(0, len(blocks_buf), self._block_size):
            block = blocks_buf[idx:idx+self._block_size]
            blocks.append(block)

        return (blocks, message_len)

    def receive(self, identifier):
        """Receive a message with an associate identifier."""

        decoder = None

        key = hashlib.sha1(identifier).digest()[:16]
        decrypter = AES.new(key)

        tasks = self._task_database.lookup(identifier)
        random.shuffle(tasks)

        for task in tasks:
            vectors = task.execute_receive()

            for vector in vectors:
                if vector.is_encoded():
                    ciphertext = vector.decode()
                    try:
                        payload = decrypter.decrypt(ciphertext)
                    except:
                        continue

                    (blocks, data_len) = self._get_blocks(payload)

                    if decoder is None:
                        decoder = coder.Decoder(self._block_size, self._block_id_bytes, data_len)

                    for block in blocks:
                        decoder.process_block(block)

                    try:
                        data = decoder.message_data()
                    except ValueError:
                        pass
                    else:
                        pdb.set_trace()
                        return self._decode_data(data)

        raise MessageLayerError('Could not receive message using available tasks')
        
class Task(object):
    """A type for Collage tasks. This is used in the task database."""

    def __init__(self, send_snippet, receive_snippet, can_embed_snippet):
        self._send_snippet = send_snippet
        self._receive_snippet = receive_snippet
        self._can_embed_snippet = can_embed_snippet

    def execute_send(self, vector):
        self._send_snippet.execute({'data': vector.get_data()})

    def execute_receive(self):
        return self._receive_snippet.execute({})

    def execute_can_embed(self, vector):
        return self._can_embed_snippet.execte({'vector': vector})

    def _hash(self):
        code = self._receive_snippet._code + self._send_snippet._code
        return hashlib.sha1(code).digest()

    def __cmp__(self, other):
        return cmp(self._hash(), other._hash())

class TaskDatabase(object):
    """An implementation of Collage's task database."""

    class MI(str):
        def _hash(self):
            return hashlib.sha1(self).digest()

        def __cmp__(self, other):
            return cmp(self._hash(), other._hash())

    def __init__(self, tasks=[], mapping_size=1):
        self._mapping_size = mapping_size
        self._tasks = tasks
        self._tasks.sort()

    def add(self, task):
        idx = bisect.bisect_left(self._tasks, task)
        if idx == len(self._tasks) or self._tasks[idx] != task:
            bisect.insort(self._tasks, task)

    def remove(self, task):
        idx = bisect.bisect_left(self._tasks, task)
        if idx < len(self._tasks) and self._tasks[idx] == task:
            del self._tasks[idx]

    def lookup(self, identifier):
        if len(self._tasks) <= self._mapping_size:
            return self._tasks[:]
        idx = bisect.bisect(self._tasks, TaskDatabase.MI(identifier))
        mapping = self._tasks[idx:idx+self._mapping_size]
        if idx + self._mapping_size > len(self._tasks):
            mapping += self._tasks[0 : idx+self._mapping_size-len(self._tasks)]
        return mapping

def main():
    def random_string():
        chars = []
        for i in range(0, 10):
            chars.append(chr(random.randrange(ord('a'), ord('z'))))
        return ''.join(chars)

    db = TaskDatabase(2)

    print 'Creating tasks'
    for i in range(10):
        db.add(Task(random_string()))

    for task in db._tasks:
        print '%s: %s' % (task.code, task._hash().encode('hex'))

    print
    print 'Testing some messages'

    for i in range(10):
        msg = random_string()
        print '%s maps to %s' % (Task(msg)._hash().encode('hex'), map(lambda t: t._hash().encode('hex'), db.lookup(msg)))

if __name__ == '__main__':
    main()
