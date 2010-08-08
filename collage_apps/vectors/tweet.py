import base64

from collage.vectorlayer import Vector, EncodingError

import pdb

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
        pdb.set_trace()

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
    def __init__(self, data):
        self._data = data
        super(CapitalizationVector, self).__init__(data)

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
