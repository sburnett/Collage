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

class MessageLayer(object):
    """Implementation of Collage's message layer. You must provide
    several parameters to this layer to use it in your application.
    
    Details not present in the paper:
    * Message sizes are powers of 2; This layer transparently handles extending
        messages to the next power of 2 if necessary, so application developers
        need not worry about this.
    * Erasure code block sizes are also powers of 2. The block size for a given
        message is derived from its length.
    """

    compression_threshold = 256

    def __init__(self, Vector, task_database, vector_provider, use_compression):
        """Initialize a message, using a particular Vector for storing message chunks."""

        self._Vector = Vector
        self._task_database = task_database
        self._vector_provider = vector_provider
        self._use_compression = use_compression

    def _choose_block_size(self, message_size):
        """Block sizes must be multiples of 2"""
        optsize = message_size/100
        realsize = 1
        while realsize < optsize:
            realsize <<= 1
        return max(min(realsize, 16), 1024)

    int_bytes = struct.calcsize('I')
    short_bytes = struct.calcsize('H')
    char_bytes = struct.calcsize('B')
    format_flags = {int_bytes: 'I',
                    short_bytes: 'H',
                    char_bytes: 'B'}

    def _sender_get_preamble_size(self, data_len):
        if data_len + self.char_bytes < (1 << self.char_bytes*8):
            return self.char_bytes
        elif data_len + self.short_bytes < (1 << self.short_bytes*8):
            return self.short_bytes
        elif data_len + self.int_bytes < (1 << self.int_bytes*8):
            return self.int_bytes
        else:
            raise ValueError('Message too big')

    def _format_message_data(self, data):
        """Pad a message with zeroes out to the nearest power of two, and store
            the length of the pad at the front of the message."""
        preamble_len = self._sender_get_preamble_size(len(data))
        format_flag = self.format_flags[preamble_len]
        data_len = len(data) + preamble_len
        real_len = 1
        while real_len < data_len:
            real_len <<= 1
        format_string = '%c%ds' % (format_flag, real_len - preamble_len)
        formatted_data = struct.pack(format_string, real_len - data_len, data)
        return formatted_data

    def _get_preamble_size(self, data_len):
        if data_len < (1 << self.char_bytes*8):
            return self.char_bytes
        elif data_len < (1 << self.short_bytes*8):
            return self.short_bytes
        elif data_len < (1 << self.int_bytes*8):
            return self.int_bytes
        else:
            raise ValueError('Message too big')

    def send(self, identifier, data, num_vectors):
        """Send a message with an associated identifier."""

        formatted_data = self._format_message_data(data)
        block_size = self._choose_block_size(len(formatted_data))
        preamble = int(log(len(formatted_data), 2))
        encoder = coder.Encoder(formatted_data, block_size)
        tasks = self._task_database.lookup(identifier)

        key = hashlib.sha1(identifier).digest()
        encrypter = AES.new(key)

        for i in range(num_vectors):
            (vector, task) = self._vector_provider.get_vector(tasks)

            def encode_vector(num_blocks):
                blocks = []
                for j in range(blocks_encoded):
                    blocks.append(encoder.next_block())
                blocks_len = len(blocks)*block_size
                payload = struct.pack('B%ds' % blocks_len, preamble, ''.join(blocks))
                if self._use_compression:
                    payload = bz2.compress(payload)
                ciphertext = encrypter.encrypt(payload)
                vector.encode(ciphertext)

            blocks_encoded = 1
            while True:
                try:
                    encode_vector(blocks_encoded)
                except vector.EncodingError:
                    break
                else:
                    blocks_encoded <<= 1

            blocks_encoded >>= 1
            if blocks_encoded == 0:
                self._vector_provider.repurpose_vector(vector)
                continue

            encode_vector(blocks_encoded)

            task.send(vector)

    def _decode_data(self, data):
        preamble_len = self._get_preamble_size(len(data))
        preamble_flag = self.format_flags[preamble_len]
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
            vectors = task.receive()

            for vector in vectors:
                if vector.is_encoded():
                    ciphertext = vector.decode()
                    if self._use_compression:
                        ciphertext = bz2.decompress(ciphertext)

                    try:
                        plaintext = decrypter.decrypt(ciphertext)
                    except:
                        continue

                    payload = plaintext[1:]

                    if decoder is None:
                        data_len = 2**payload[0]
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
        
class TaskDatabase(object):
    """An implementation of Collage's task database."""

    class MI(str):
        def hash(self):
            return hashlib.sha1(self).digest()

    def __init__(self, mapping_size=1, tasks=[]):
        self.mapping_size = mapping_size
        self.tasks = tasks
        self.tasks.sort()

    def add(self, task):
        idx = bisect.bisect_left(self.tasks, task)
        if idx == len(self.tasks) or self.tasks[idx] != task:
            bisect.insort(self.tasks, task)

    def remove(self, task):
        idx = bisect.bisect_left(self.tasks, task)
        if idx < len(self.tasks) and self.tasks[idx] == task:
            del self.tasks[idx]

    def lookup(self, identifier):
        idx = bisect.bisect(self.tasks, TaskDatabase.MI(identifier))
        mapping = self.tasks[idx:idx+self.mapping_size]
        if idx + self.mapping_size > len(self.tasks):
            mapping += self.tasks[0:idx+self.mapping_size-len(self.tasks)]
        return mapping

class Task(object):
    """A type for Collage tasks. This is used in the task database."""

    def __init__(self, send_snippet, receive_snippet):
        self._send_snippet = send_snippet
        self._receive_snippet = receive_snippet

    def send(self, vector):
        self._send_snippet.execute({'data': vector.get_data()})

    def receive(self):
        return self._receive_snippet.execute({})

    def hash(self):
        code = self._receive_snippet.get_code() + self._send_snippet.get_code()
        return hashlib.sha1(code).digest()

    def __cmp__(self, other):
        return cmp(self.hash(), other.hash())

def load_tasks():
    tasks = []
    all_snippets = snippets.load_python_snippets()
    for task_name, snippets in all_snippets.items():
        send_snippet = snippets['send_snippet']
        receive_snippet = snippets['receive_snippet']
        task = Task(send_snippet, receive_snippet)
        tasks.append(task)
    return tasks

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

    for task in db.tasks:
        print '%s: %s' % (task.code, task.hash().encode('hex'))

    print
    print 'Testing some messages'

    for i in range(10):
        msg = random_string()
        print '%s maps to %s' % (Task(msg).hash().encode('hex'), map(lambda t: t.hash().encode('hex'), db.lookup(msg)))

if __name__ == '__main__':
    main()
