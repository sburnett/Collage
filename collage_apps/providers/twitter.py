from collage.vectorlayer import VectorProvider

class UniformTweetProvider(VectorProvider):
    def __init__(self, VectorClass):
        self._VectorClass = VectorClass
        VectorProvider.__init__(self)
        self._vectors.append(self._VectorClass('a'*155))

    def _find_vector(self, task):
        vector = self._VectorClass('a'*155)
        self._vectors.append(vector)
        return vector
