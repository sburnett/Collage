import hashlib
from Crypto.Cipher import AES
import bisect
import struct
import random
from math import log
import bz2

import coder
import snippets
import vector
import vectorprovider

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

    _header_compressed_mask = 1 << _char_bytes*8 - 1
    _header_size_mask = 1 << ~(_char_bytes*8 - 1)

    def __init__(self, vector_provider, block_size, snippet_dirs, task_mapping_size):
        """Initialize a message, using a particular Vector for storing message chunks."""

        self._vector_provider = vector_provider
        self._block_size = block_size

        self._task_mapping_size = task_mapping_size
        self._snippet_dirs = snippet_dirs
        self.reload_task_database()

    def reload_task_database(self):
        all_snippets = snippets.load_snippets(self._snippet_dirs)
        tasks = []
        for (send_snippet, receive_snippet, can_embed_snippet) in all_snippets:
            task = Task(send_snippet, receive_snippet, can_embed_snippet)
            tasks.append(task)
        self._task_database = TaskDatabase(tasks, self._task_mapping_size)

    def _choose_block_size(self, message_size):
        """Block sizes must be multiples of 2"""
        optsize = message_size/100
        realsize = 1
        while realsize < optsize:
            realsize <<= 1
        return max(min(realsize, 16), 1024)

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
        while real_len < data_len:
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

    def send(self, identifier, data, num_vectors):
        """Send a message with an associated identifier."""

        tasks = self._task_database.lookup(identifier)

        formatted_data = self._format_message_data(data)
        encoder = coder.Encoder(formatted_data, self._block_size)

        key = hashlib.sha1(identifier).digest()
        encrypter = AES.new(key)

        header = int(log(len(formatted_data), 2))
        compressed_header = self._header_compressed_mask | header

        for i in range(num_vectors):
            (cover_vector, task) = self._vector_provider.get_vector(tasks)

            blocks_encoded = 1
            while True:
                blocks = []
                for j in range(blocks_encoded):
                    blocks.append(encoder.next_block())
                blocks_buf = ''.join(blocks)
                compressed_blocks_buf = bz2.compress(blocks_buf)
                if len(blocks_buf) <= len(compressed_blocks_buf):
                    blocks_len = len(blocks_buf)
                    payload = struct.pack('B%ds' % blocks_len,
                                          header,
                                          blocks_buf)
                else:
                    blocks_len = len(compressed_blocks_buf)
                    payload = struct.pack('B%ds' % blocks_len,
                                          compressed_header,
                                          compressed_blocks_buf)
                ciphertext = encrypter.encrypt(payload)
                try:
                    coded_vector = cover_vector.encode(ciphertext)
                except vector.EncodingError:
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
        preamble = struct.unpack(preamble_flag, data[:preamble_len])
        padding_len = 2**preamble
        return data[preamble_len : len(data) - padding_len]

    def receive(self, identifier):
        """Receive a message with an associate identifier."""

        decoder = None

        key = hashlib.sha1(identifier).digest()
        decrypter = AES.new(key)

        tasks = self._task_database.lookup(identifier)
        random.shuffle(tasks)

        for task in tasks:
            vectors = task.execute_receive()

            for vector in vectors:
                if vector.is_encoded():
                    ciphertext = vector.decode()
                    header_compress = ciphertext[0] & self._header_compressed_mask
                    header_len = ciphertext[0] & self._header_size_mask
                    if header_compress != 0:
                        ciphertext = bz2.decompress(ciphertext)

                    try:
                        plaintext = decrypter.decrypt(ciphertext)
                    except:
                        continue

                    payload = plaintext[1:]

                    if decoder is None:
                        data_len = 2**header_len
                        block_size = self._choose_block_size(data_len)
                        decoder = coder.Decoder(block_size, data_len)

                    for idx in range(0, len(payload), block_size):
                        block = payload[idx:idx+block_size]
                        decoder.process_block(block)

                    try:
                        data = decoder.message_data()
                    except ValueError:
                        pass
                    else:
                        return self._decode_data(data)

        return None
        
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
        code = self._receive_snippet.get_code() + self._send_snippet.get_code()
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
