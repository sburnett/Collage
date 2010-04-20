import hashlib
from Crypto.Cipher import ARC4
import bisect
import struct
import random
from math import log, ceil
import bz2

import coder
import vectorlayer

import pdb

class MessageLayerError(Exception):
    pass

class MessageLayer(object):
    """Implementation of Collage's message layer. You must provide
    several parameters to this layer to use it in your application.
    
    Details not present in the paper:
    * Message sizes are powers of 2; This class transparently handles extending
        messages to the next power of 2 if necessary, so application developers
        need not worry about this.
    * Erasure code block sizes are also powers of 2.
    * The message format is as follows: the message is padded with zeroes to
        the next power of two, including the padding header. The padding header
        contains the length of the padding appended to the message."""

    _int_bytes = struct.calcsize('I')
    _short_bytes = struct.calcsize('H')
    _char_bytes = struct.calcsize('B')
    _format_flags = {_int_bytes: 'I',
                    _short_bytes: 'H',
                    _char_bytes: 'B'}

    _header_compressed_mask = 0x80
    _header_size_mask = 0x7F

    def __init__(self, vector_provider, block_size, max_unique_blocks,
                 tasks, task_mapping_size, instrument=None, error_margin=2):
        """Initialize a message, using a particular Vector
            for storing message chunks."""

        self._vector_provider = vector_provider
        self._block_size = block_size
        self._block_id_bytes = int(ceil(log(max_unique_blocks, 2)/8))

        self._task_mapping_size = task_mapping_size
        self.reload_task_database(tasks)

        if instrument is None:
            self._instrument = lambda s: None
        else:
            self._instrument = instrument

        self._error_margin = error_margin

    def reload_task_database(self, tasks):
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
            payload = struct.pack('B%ds' % (len(blocks_buf),),
                                  header,
                                  blocks_buf)
        else:
            compressed_header = self._header_compressed_mask | header
            payload = struct.pack('B%ds' % (len(compressed_blocks_buf),),
                                  compressed_header,
                                  compressed_blocks_buf)
        return payload

    def send(self, identifier, data, num_vectors=0, send_ratio=1):
        """Send a message with an associated identifier."""

        self._instrument('begin send')
    
        tasks = self._task_database.lookup(identifier)

        formatted_data = self._format_message_data(data)
        data_len = len(formatted_data)
        encoder = coder.Encoder(formatted_data, self._block_size, self._block_id_bytes)

        key = hashlib.sha1(identifier).digest()

        if num_vectors > 0:
            vector_counter = 0
        else:
            bytes_sent = 0
            total_bytes = data_len*send_ratio
            self._instrument('will upload %d bytes' % total_bytes)

        while True:
            if num_vectors > 0:
                if vector_counter >= num_vectors:
                    break
                vector_counter += 1
            elif bytes_sent >= total_bytes:
                break

            vector_result = self._vector_provider.get_vector(tasks)
            if vector_result is None:
                self._instrument('end send')
                self._instrument('send failure')
                raise MessageLayerError('Unable to acquire enough vectors')
            (cover_vector, task) = vector_result

            def encode_vector(num_blocks):
                blocks = []
                for i in range(0, num_blocks):
                    blocks.append(encoder.next_block())

                payload = self._prepare_payload(blocks, data_len)
                encrypter = ARC4.new(key)
                ciphertext = encrypter.encrypt(payload)

                print 'Attempting to encode %d bytes' % (len(ciphertext),)

                self._instrument('begin encode')
                try:
                    coded_vector = cover_vector.encode(ciphertext, key)
                except vectorlayer.EncodingError:
                    raise vectorlayer.EncodingError
                finally:
                    self._instrument('end encode')

                return (len(ciphertext), coded_vector)

            coded_vector = None
            lower_bound = upper_bound = 2
            while True:
                try:
                    (current_len, coded_vector) = encode_vector(upper_bound)
                except vectorlayer.EncodingError:
                    break
                else:
                    lower_bound = upper_bound
                    upper_bound *= 2

            while upper_bound - lower_bound > self._error_margin:
                current_size = lower_bound + (upper_bound - lower_bound)/2
                try:
                    (current_len, coded_vector) = encode_vector(current_size)
                except vectorlayer.EncodingError:
                    upper_bound = current_size
                else:
                    lower_bound = current_size

            if coded_vector:
                self._instrument('upload %d bytes in %d byte cover' % (current_len, len(coded_vector.get_data())))
                print 'Uploading photo with %d encoded bytes' % (current_len,)
                task.send(key, coded_vector)
                if num_vectors == 0:
                    bytes_sent += current_len
                    print 'We have sent %d of %d bytes' % (bytes_sent, total_bytes)
            else:
                self._vector_provider.repurpose_vector(cover_vector)

        self._instrument('end send')
        self._instrument('send success')

    def _decode_data(self, data):
        preamble_len = self._get_preamble_size(len(data))
        preamble_flag = self._format_flags[preamble_len]
        (padding_len,) = struct.unpack(preamble_flag, data[:preamble_len])
        return data[preamble_len : len(data) - padding_len]

    def _get_blocks(self, payload):
        (header,) = struct.unpack('B', payload[0])
        blocks_buf = payload[1:]

        compressed = header & self._header_compressed_mask != 0
        message_len = 2**(header & self._header_size_mask)

        if compressed:
            blocks_buf = bz2.decompress(blocks_buf)
        else:
            payload_len = len(blocks_buf) - len(blocks_buf) % self._block_size
            blocks_buf = blocks_buf[:payload_len]

        blocks = []
        for idx in range(0, len(blocks_buf), self._block_size):
            block = blocks_buf[idx:idx+self._block_size]
            blocks.append(block)

        return (blocks, message_len)

    def receive(self, identifier):
        """Receive a message with an associate identifier."""

        self._instrument('begin receive')

        decoder = None

        key = hashlib.sha1(identifier).digest()

        tasks = self._task_database.lookup(identifier)
        random.shuffle(tasks)

        bytes_decoded = 0

        for task in tasks:
            for vector in task.receive(key):
                if vector.is_encoded(key):
                    self._instrument('begin decode')
                    ciphertext = vector.decode(key)
                    self._instrument('end decode')

                    try:
                        decrypter = ARC4.new(key)
                        payload = decrypter.decrypt(ciphertext)
                    except:
                        continue

                    bytes_decoded += len(payload)
                    self._instrument('decoded %d bytes from %d byte cover' % (bytes_decoded, len(vector.get_data())))
                    print 'Decoded %d bytes' % (bytes_decoded,)

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
                        self._instrument('end receive')
                        self._instrument('receive success')
                        return self._decode_data(data)

        self._instrument('end_receive')
        self._instrument('receive failure')
        raise MessageLayerError('Could not receive message using available tasks')
        
class Task(object):
    """A type for Collage tasks. This is used in the task database."""

    def send(self, id, vector):
        raise NotImplementedError

    def receive(self, id):
        raise NotImplementedError

    def can_embed(self, id, vector):
        raise NotImplementedError

    def _hash(self):
        return hashlib.sha1(str(hash(self))).digest()

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
