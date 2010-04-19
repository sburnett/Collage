import os.path
import random

from collage.vectorlayer import VectorProvider, EncodingError

from vectors import DonatedOutguessVector

class NullVectorProvider(VectorProvider):
    def _find_vector(self, task):
        return None

class DirectoryVectorProvider(VectorProvider):
    def __init__(self, VectorClass, directory, extensions=None):
        VectorProvider.__init__(self)

        for file in os.listdir(directory):
            (root, ext) = os.path.splitext(file)
            if os.path.isfile(os.path.join(directory, file)) and \
                    (extensions is None or ext in extensions):
                data = open(os.path.join(directory, file), 'rb').read()
                self._vectors.append(VectorClass(data))

    def _find_vector(self, task):
        if len(self._vectors) == 0:
            return None
        else:
            return random.choice(self._vectors)

class UniformTweetProvider(VectorProvider):
    def __init__(self, VectorClass):
        self._VectorClass = VectorClass
        VectorProvider.__init__(self)
        self._vectors.append(self._VectorClass('a'*155))

    def _find_vector(self, task):
        vector = self._VectorClass('a'*155)
        self._vectors.append(vector)
        return vector

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

class DonatedVectorProvider(VectorProvider):
    def __init__(self, VectorClass, database, killswitch):
        super(DonatedVectorProvider, self).__init__(self)

        self._VectorClass = VectorClass
        self._db = database
        self._killswitch = killswitch

    def _find_vector(self, task):
        if self._killswitch.is_set():
            return None

        (a, b) = task.get_tags()
        attrs = [('tag', a), ('tag', b)]
        vectors = self._db.find_vectors(attrs)

        if len(vectors) > 0:
            key = vectors[0]
            data = open(self._db.get_filename(key), 'rb').read()
            return DonatedOutguessVector(data, key)
        else:
            return None
