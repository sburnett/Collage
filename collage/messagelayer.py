"""
The core of Collage's asynchronous message channel.

Some terminology:
* A vector is some cover material used to store message data. Examples include
  JPEGs, tweets, YouTube videos, etc.
* We abbreviate user-generated content as UGC.
* Messages are split into chunks using erasure coding.
* Message chunks are embedded inside vectors using, e.g., steganography.
* Tasks are used to send and receive embedded vectors to and from
  user-generated content (UGC) hosts (e.g., Flickr, Picasa, YouTube, etc.)

"""

import hashlib
from Crypto.Cipher import ARC4
from Crypto.Hash import HMAC
import bisect
import struct
import random
from math import log, ceil
import bz2
import math

import coder
import vectorlayer
from instrument import CollageStatus

DISABLE_COMPRESSION = False

class MessageLayerError(Exception):
    """Raised when the message layer fails to send or receive a message."""
    pass

class MessageLayer(object):
    """Implementation of Collage's message layer.
    
    This module runs messages through encryption and erasure coding
    and executes tasks, but relies on applications to provide
    several external components:
    * Some vectors (e.g., JPEGs), via an instance of VectorProvider.
    * A list of tasks (e.g., "Search Flickr for 'blue flowers'").
    * Tuning parameters: erasure code block size and tasks per message.
    
    Details not present in the paper:
    * Message sizes are powers of 2; This class transparently handles extending
        messages to the next power of 2 if necessary, so application developers
        need not worry about this.
    * Erasure code block sizes are also powers of 2.
    * The message format is as follows: the message is padded with zeroes to
        the next power of two, including the padding header. The padding header
        contains the length of the padding appended to the message.
        
    """

    _header_bytes = { struct.calcsize('I'): 'I'
                    , struct.calcsize('H'): 'H'
                    , struct.calcsize('B'): 'B'
                    }

    _header_compressed_mask = 0x80
    _header_size_mask = 0x7F

    def __init__(self, vector_provider, block_size, max_unique_blocks,
                 tasks, task_mapping_size, inst=None, error_margin=2, mac=False):
        """Initialize a message channel using application specific parameters.

        These parameters are:
        * An instance VectorProvider that provides vectors (e.g., JPEGs) for
          storing message chunks.
        * The block size, for the erasure coder. A good value is 8.
        * The maximum unique blocks permitted by the coder. This should be at
          least large as the total number of blocks you expect to publish inside
          vectors on user-generated content hosts.
        * A list of Tasks used to send and receive messages.
        * The task mapping size, which is the number of tasks allotted to each
          message. A higher number spreads a message's content over a wider
          area on a content host; this provides more redundancy, but also
          forces receivers to expend more effort.

        There are several optional parameters:
        * An instance of Instrument, for performing logging and monitoring
        * An error margin in the amount of data encoded in each vector. By
          default, we perform a binary search to discover exactly how much
          content can be stored inside a vector; this parameter allows some
          inaccuracy in this search, which can significantly speed up encoding.
        * Whether or not to include a message authentication code in each
          encoded vector. If you cannot tell whether a vector contains
          message data, then you should enable this option.

        """

        self._vector_provider = vector_provider
        self._block_size = block_size
        self._block_id_bytes = int(ceil(log(max_unique_blocks, 2)/8))

        self._task_mapping_size = task_mapping_size
        self.reload_task_database(tasks)

        if inst is None:
            self._instrument = instrument.Instrument()
        else:
            self._instrument = inst

        self._error_margin = error_margin
        self._mac = mac

    def reload_task_database(self, tasks):
        self._task_database = TaskDatabase(tasks, self._task_mapping_size)

    def _sender_get_preamble_size(self, data_len):
        candidates = set()
        for header_bytes in self._header_bytes.keys():
            candidate = int(math.log(header_bytes + data_len, 2)/8 + 1)
            if candidate <= header_bytes:
                candidates.add(header_bytes)
        try:
            return min(candidates)
        except ValueError:
            raise ValueError('Message too big')

    def _format_message_data(self, data):
        """Pad a message with zeroes out to the nearest power of two.
        
        We store the length of the pad at the front of the message.
        
        """

        preamble_len = self._sender_get_preamble_size(len(data))
        format_flag = self._header_bytes[preamble_len]
        data_len = len(data) + preamble_len
        real_len = 1
        while real_len <= max(data_len, self._block_size):
            real_len <<= 1
        real_len -= 1
        format_string = '%c%ds' % (format_flag, real_len - preamble_len)
        formatted_data = struct.pack(format_string, real_len - data_len, data)
        return formatted_data

    def _get_preamble_size(self, data_len):
        candidates = set()
        for header_bytes in self._header_bytes.keys():
            candidate = int(math.log(data_len, 2)/8 + 1)
            if candidate <= header_bytes:
                candidates.add(header_bytes)
        try:
            return min(candidates)
        except ValueError:
            raise ValueError('Message too big')

    def _prepare_payload(self, blocks, message_len):
        blocks_buf = ''.join(blocks)
        header = int(log(message_len, 2))

        compressed_blocks_buf = bz2.compress(blocks_buf)
        if len(blocks_buf) <= len(compressed_blocks_buf) \
                or DISABLE_COMPRESSION:
            print 'Not using compression'
            payload = struct.pack('B%ds' % (len(blocks_buf),),
                                  header,
                                  blocks_buf)
        else:
            print 'Using compression'
            compressed_header = self._header_compressed_mask | header
            payload = struct.pack('B%ds' % (len(compressed_blocks_buf),),
                                  compressed_header,
                                  compressed_blocks_buf)
        return payload

    def send(self, identifier, data, num_vectors=0, send_ratio=1):
        """Send a message with an associated identifier.
        
        The same identifier must be used by the receiver. It is
        the application's responsibility to make sure the receiver
        knows the identifier.
        
        Roughly, this method stores the message inside vectors
        and uploads them to user-generated content hosts. There
        are two ways of limiting how many vectors are uploaded:
        * Specifying a hard limit on the number of vectors (num_vectors).
        * Specifying how many message blocks should be uploaded (send_ratio). A
          value of 1 means "send exactly enough message blocks to reconstruct
          the message", a value of 2 means "send twice as many blocks
          as required", etc.

        """

        self._instrument.change_status(CollageStatus.INIT)
    
        tasks = self._task_database.lookup(identifier)
        print 'Sending using tasks:'
        for task in tasks:
            print task

        formatted_data = self._format_message_data(data)
        data_len = len(formatted_data)+1
        encoder = coder.Encoder(formatted_data, self._block_size, self._block_id_bytes)

        key = hashlib.sha1(identifier).digest()

        if num_vectors > 0:
            vector_counter = 0
        else:
            bytes_sent = 0
            total_bytes = data_len*send_ratio
            print 'Will upload %d bytes' % total_bytes

        while True:
            if num_vectors > 0:
                if vector_counter >= num_vectors:
                    break
                vector_counter += 1
            elif bytes_sent >= total_bytes:
                break

            vector_result = self._vector_provider.get_vector(tasks)
            if vector_result is None:
                self._instrument.change_status(CollageStatus.FAILURE)
                raise MessageLayerError('Unable to acquire enough vectors')
            (cover_vector, task) = vector_result

            def encode_vector(num_blocks):
                blocks = []
                for i in range(0, num_blocks):
                    blocks.append(encoder.next_block())

                self._instrument.change_status(CollageStatus.ENCODING)
                payload = self._prepare_payload(blocks, data_len)
                self._instrument.change_status(CollageStatus.ENCRYPTING)
                ciphertext = ARC4.new(key).encrypt(payload)
                if self._mac:
                    mac = HMAC.new(identifier, msg=ciphertext).digest()
                    ciphertext = '%s%s' % (mac, ciphertext)

                print 'Attempting to embed %d bytes' % (len(ciphertext),)

                try:
                    self._instrument.change_status(CollageStatus.EMBEDDING)
                    encoded_vector = cover_vector.encode(ciphertext, key)
                    print 'GOTVECTOR: %s' % hashlib.md5(encoded_vector.get_data()).hexdigest()
                except vectorlayer.EncodingError:
                    raise vectorlayer.EncodingError

                return (len(ciphertext), encoded_vector)

            try:
                lower_bound = upper_bound = cover_vector.estimate_max_capacity()
            except NotImplementedError:
                lower_bound = upper_bound = 2

            # Step 1: Find a rough lower bound by continuously halving
            # the estimate until we can successfully encode something.
            coded_vector = None
            while lower_bound > 2:
                current_size = lower_bound
                try:
                    (current_len, coded_vector) = encode_vector(current_size)
                except vectorlayer.EncodingError:
                    upper_bound = lower_bound
                    lower_bound /= 2
                else:
                    break

            # Step 2: Find a rough upper bound by adjusting the upper
            # (and lower) bounds in ever-increasing increments.
            increment = 1
            while True:
                current_size = upper_bound
                try:
                    (current_len, coded_vector) = encode_vector(current_size)
                except vectorlayer.EncodingError:
                    break
                else:
                    increment *= 2
                    lower_bound = upper_bound
                    upper_bound += increment

            # Step 3: Continuously tighten bounds until
            # within the margin, using binary search.
            while upper_bound - lower_bound > self._error_margin:
                current_size = lower_bound + (upper_bound - lower_bound)/2
                try:
                    (current_len, coded_vector) = encode_vector(current_size)
                except vectorlayer.EncodingError:
                    upper_bound = current_size
                else:
                    lower_bound = current_size

            if coded_vector:
                try:
                    cover_vector.record_estimate(current_size)
                except AttributeError:
                    pass

                print 'Uploading photo with %d encoded bytes' % (current_len,)
                print 'UPLOADING: %s' % hashlib.md5(coded_vector.get_data()).hexdigest()
                print 'To upload length: %d' % len(coded_vector._data)
                self._instrument.change_status(CollageStatus.UPLOADING)
                task.send(key, coded_vector)
                self._instrument.upload_vector(len(coded_vector.get_data()))
                self._instrument.upload_chunks(current_len)
                if num_vectors == 0:
                    bytes_sent += current_len
                    print 'We have sent %d of %d bytes' % (bytes_sent, total_bytes)
            else:
                self._vector_provider.repurpose_vector(cover_vector)

        self._instrument.change_status(CollageStatus.SUCCESS)

    def _decode_data(self, data):
        preamble_len = self._get_preamble_size(len(data))
        preamble_flag = self._header_bytes[preamble_len]
        (padding_len,) = struct.unpack(preamble_flag, data[:preamble_len])
        return data[preamble_len : len(data) - padding_len + 1]

    def _get_blocks(self, payload):
        (header,) = struct.unpack('B', payload[0])
        blocks_buf = payload[1:]

        compressed = header & self._header_compressed_mask != 0
        message_len = 2**(header & self._header_size_mask) - 1

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

        self._instrument.change_status(CollageStatus.INIT)

        decoder = None

        key = hashlib.sha1(identifier).digest()

        tasks = self._task_database.lookup(identifier)
        random.shuffle(tasks)

        bytes_decoded = 0

        self._instrument.change_status(CollageStatus.DOWNLOADING)
        for task in tasks:
            for vector in task.receive(key):
                self._instrument.process_vector(len(vector.get_data()))

                if vector.is_encoded(key):
                    self._instrument.change_status(CollageStatus.EXTRACTING)
                    ciphertext = vector.decode(key)

                    if self._mac:
                        try:
                            digester = HMAC.new(identifier)
                            mac = ciphertext[:digester.digest_size]
                            ciphertext = ciphertext[digester.digest_size:]

                            digester.update(ciphertext)
                            if digester.digest() != mac:
                                print 'MAC is not authentic'
                                self._instrument.change_status(CollageStatus.DOWNLOADING)
                                continue
                        except:
                            self._instrument.change_status(CollageStatus.DOWNLOADING)
                            continue

                    try:
                        self._instrument.change_status(CollageStatus.DECRYPTING)
                        decrypter = ARC4.new(key)
                        payload = decrypter.decrypt(ciphertext)
                    except:
                        self._instrument.change_status(CollageStatus.DOWNLOADING)
                        continue

                    bytes_decoded += len(payload)
                    print 'Decoded %d bytes' % (bytes_decoded,)

                    (blocks, data_len) = self._get_blocks(payload)

                    if decoder is None:
                        decoder = coder.Decoder(self._block_size, self._block_id_bytes, data_len)

                    self._instrument.change_status(CollageStatus.DECODING)
                    for block in blocks:
                        self._instrument.process_chunks(len(block))
                        decoder.process_block(block)

                    try:
                        data = decoder.message_data()
                    except ValueError:
                        pass
                    else:
                        self._instrument.change_status(CollageStatus.SUCCESS)
                        return self._decode_data(data)

                    self._instrument.change_status(CollageStatus.DOWNLOADING)

        self._instrument.change_status(CollageStatus.FAILURE)
        raise MessageLayerError('Could not receive message using available tasks')
        
class Task(object):
    """Tasks used to upload and download vectors on UGC hosts.
    
    You will need to implement a bunch of these for your application.

    """

    def send(self, id, vector):
        """Upload a vector using this task.

        The vector should be embedded with data for the message
        with the given identifier. For example, this method might
        upload pictures to a Flickr account.

        """
        raise NotImplementedError

    def receive(self, id):
        """Download vectors using this task.

        The task will search for vectors containing data for the given identier.
        For example, it might search Flickr for "blue flowers" and download
        all the search results.

        """
        raise NotImplementedError

    def can_embed(self, id, vector):
        """Decide whether a particular vector can be used with this task.

        Not all vectors can be used with a given task. For example, if this task
        searches for pictures of "blue flowers", then this method should only
        accept vectors that have blue flowers. This can be enforced with
        properties of the vectors.

        """
        raise NotImplementedError

    def _hash(self):
        return hashlib.sha1(str(hash(self))).digest()

    def __cmp__(self, other):
        return cmp(self._hash(), other._hash())

class TaskDatabase(object):
    """An implementation of Collage's task database.
    
    This class is used by the MessageLayer. You shouldn't need
    to instantiate this class yourself.
    
    """

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
