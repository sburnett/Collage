import os.path
import random

from collage.vectorlayer import VectorProvider

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
