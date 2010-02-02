import os.path
import random

from collage.vectorlayer import VectorProvider, EncodingError

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
