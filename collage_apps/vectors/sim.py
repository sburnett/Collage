import struct

from collage.vectorlayer import Vector, EncodingError

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
