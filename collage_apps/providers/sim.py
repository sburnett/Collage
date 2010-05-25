import random

from collage.vectorlayer import VectorProvider

class SimulatedVectorProvider(VectorProvider):
    def __init__(self, VectorClass, encoding_rate, encoding_deviation,
                                    vector_length, vector_deviation):
        VectorProvider.__init__(self)
        self._VectorClass = VectorClass
        self._encoding_rate = encoding_rate
        self._encoding_deviation = encoding_deviation
        self._vector_length = vector_length
        self._vector_deviation = vector_deviation
        self._tries_left = 200

    def _find_vector(self, task):
        if self._tries_left == 0:
            return None
        else:
            self._tries_left -= 1
        veclen = int(random.gauss(self._vector_length, self._vector_deviation))
        rate = random.gauss(self._encoding_rate, self._encoding_deviation)
        vector = self._VectorClass(' '*veclen, rate)
        self._vectors.append(vector)
        return vector
