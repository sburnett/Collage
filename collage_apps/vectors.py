import subprocess
import tempfile
import base64
import time
import struct

import hashlib
import pdb

from collage.vectorlayer import Vector, EncodingError

class OutguessVector(Vector):
    def __init__(self, data, timeout=10):
        super(OutguessVector, self).__init__(data)
        self._timeout = timeout
        self._decoded_data = None

    def encode(self, message, key):
        data_file = tempfile.NamedTemporaryFile()
        data_file.write(message)
        data_file.flush()

        cover_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        cover_file.write(self._data)
        cover_file.flush()

        dest_file = tempfile.NamedTemporaryFile(suffix='.jpg')

        command = ['outguess', '-k', base64.b64encode(key), 
                   '-d', data_file.name,
                   cover_file.name, dest_file.name]
        proc = subprocess.Popen(command, stdout=open('/dev/null', 'w'),
                                         stderr=subprocess.STDOUT)

        time_left = self._timeout
        poll_interval = 1
        while time_left > 0 and proc.poll() is None:
            time.sleep(poll_interval)
            time_left -= poll_interval

        if proc.returncode is None or proc.returncode != 0:
            if proc.returncode is None:
                proc.terminate()
            raise EncodingError

        encoded = dest_file.read()
        encoded_vector = OutguessVector(encoded)

        if encoded_vector.decode(key) != message:
            raise EncodingError

        print 'RETURNING: %s' % hashlib.md5(encoded_vector.get_data()).hexdigest()
        return encoded_vector

    def decode(self, key):
        print 'Key: %s' % base64.b64encode(key)
        print 'Image hash: %s' % hashlib.md5(self._data).hexdigest()
        if self._decoded_data is None:
            embedded_file = tempfile.NamedTemporaryFile(suffix='.jpg')
            embedded_file.write(self._data)
            embedded_file.flush()
            data_file = tempfile.NamedTemporaryFile()

            print '!DC image: ' + hashlib.md5(open(embedded_file.name, 'r').read()).hexdigest()
            print '!DC length: ' + str(len(open(embedded_file.name, 'r').read()))

            command = ['outguess', '-k', base64.b64encode(key),
                       '-r', embedded_file.name,
                       data_file.name]
            print '!DC command: ' + str(command)
            retcode = subprocess.call(command, stdout=open('/dev/null', 'w'),
                                               stderr=subprocess.STDOUT)

            if retcode != 0:
                return None

            self._decoded_data = data_file.read()
            print '!DC data: %s' % hashlib.md5(self._decoded_data).hexdigest()

        return self._decoded_data

    def is_encoded(self, key):
        return self.decode(key) is not None

    def __cmp__(self, other):
        return cmp(self._data, other._data)

class DonatedOutguessVector(OutguessVector):
    def __init__(self, data, key):
        super(DonatedOutguessVector, self).__init__(data)
        self._key = key

    def encode(self, data, key):
        vec = super(DonatedOutguessVector, self).encode(data, key)
        return DonatedOutguessVector(vec.get_data(), self._key)

    def get_key(self):
        return self._key

class BlatantVector(Vector):
    def __init__(self, data):
        super(BlatantVector, self).__init__(data)
        self._key_bytes = 4

    def encode(self, data, id):
        edata = base64.b64encode(id[:self._key_bytes] + data)
        if len(edata) > 140:
            raise EncodingError
        else:
            return BlatantVector(edata)

    def decode(self, id):
        if not self.is_encoded(id):
            return None

        return base64.b64decode(self._data)[self._key_bytes:]

    def is_encoded(self, id):
        return base64.b64decode(self._data)[:self._key_bytes] == id[:self._key_bytes]

    def get_property(self, key):
        return {'length': len(self._data)}

    def __cmp__(self, other):
        return cmp(self._data, other._data)

class AllCapsVector(Vector):
    def __init__(self, data):
        super(AllCapsVector, self).__init__(data)
        self._key_chars = 1

    def encode(self, data, id):
        key = base64.b64encode(id)[:self._key_chars]

        bit_mask = 1
        byte_counter = 0

        cover = self._data
        num_bits = 0
        for c in cover:
            if c.isalpha():
                num_bits += 1

        if num_bits < len(data)*8:
            raise EncodingError

        encoded = []
        for i in range(len(cover)):
            if cover[i].isalpha():
                if byte_counter < len(data):
                    bit = (ord(data[byte_counter]) & bit_mask) != 0
                    if bit:
                        encoded.append(cover[i].upper())
                    else:
                        encoded.append(cover[i].lower())
                    bit_mask <<= 1
                    if bit_mask >= 256:
                        bit_mask = 1
                        byte_counter += 1
            else:
                encoded.append(cover[i])

        return AllCapsVector(key + ''.join(encoded))

    def decode(self, key):
        bits = []

        cover = self._data[self._key_chars:]
        for i in range(len(cover)):
            if cover[i].isalpha():
                if cover[i].isupper():
                    bits.append(1)
                else:
                    bits.append(0)

        for i in range(len(bits)):
            bits[i] <<= (i % 8)

        message = []
        for i in range(0, len(bits), 8):
            message.append(chr(sum(bits[i:i+8])))

        message = ''.join(message)
        return message

    def is_encoded(self, key):
        key = base64.b64encode(id)[:self._key_chars]
        return self._data[:self._key_chars] == key[:self._key_chars]

    def get_property(self, key):
        return {'length': len(self._data)}

    def __cmp__(self, other):
        return cmp(self._data, other._data)

class CapitalizationVector(Vector):
    def encode(self, data, key):
        cover = self._data
        num_bits = 0
        prev_nonalpha = True
        for c in cover:
            if c.isalpha() and prev_nonalpha:
                num_bits += 1

            prev_nonalpha = not c.isalpha()

        if num_bits < len(data)*8:
            raise EncodingError

        bit_mask = 1
        byte_counter = 0

        prev_nonalpha = True
        encoded = []
        for i in range(len(cover)):
            if cover[i].isalpha() and prev_nonalpha:
                if byte_counter < len(data):
                    bit = (ord(data[byte_counter]) & bit_mask) != 0
                    if bit:
                        encoded.append(cover[i].upper())
                    else:
                        encoded.append(cover[i].lower())
                    bit_mask <<= 1
                    if bit_mask >= 256:
                        bit_mask = 1
                        byte_counter += 1
            else:
                encoded.append(cover[i])

            prev_nonalpha = not cover[i].isalpha()

        return CapitalizationVector(''.join(encoded))

    def decode(self, key):
        bits = []

        prev_nonalpha = True
        cover = self._data
        for i in range(len(cover)):
            if cover[i].isalpha() and prev_nonalpha:
                if cover[i].isupper():
                    bits.append(1)
                else:
                    bits.append(0)

            prev_nonalpha = False

        for i in range(len(bits)):
            bits[i] <<= (i % 8)

        message = []
        for i in range(0, len(bits), 8):
            message.append(chr(sum(bits[i:i+8])))

        message = ''.join(message)
        return message

    def is_encoded(self, key):
        return True

    def get_property(self, key):
        return {'length': len(self._data)}

    def __cmp__(self, other):
        return cmp(self._data, other._data)

class SimulatedVector(Vector):
    def __init__(self, data, rate):
        super(SimulatedVector, self).__init__(data)
        self._rate = rate

    def encode(self, data, id):
        if self._rate*len(self._data) < len(data):
            raise EncodingError
        datalen = len(data)
        edata = struct.pack('I%ds' % len(self._data), len(data), data)
        return SimulatedVector(edata, self._rate)

    def decode(self, id):
        (datalen,) = struct.unpack('I', self._data[:4])
        data = self._data[4:datalen+4]
        return data

    def is_encoded(self, id):
        return True

    def get_property(self, key):
        return {}

    def __cmp__(self, other):
        return cmp(self._data, other._data)
