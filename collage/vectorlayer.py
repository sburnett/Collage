import random

class EncodingError(Exception):
    """This error is raised when some data cannot be encoded
    into a vector. The most common reason for this error is
    that the steganography/watermarking/other algorithm doesn't
    have enough space to fit the data in the amount of space
    available."""
    pass

class Vector(object):
    """An abstract class for an immutable vector; encoding and decoding should
    create new copies of the vector."""

    def __init__(self, data, properties={}):
        self._data = str(data)
        self._properties = dict(properties)

    def get_data(self):
        return self._data

    def get_property(self, key):
        return self._properties[key]

    def encode(self, data, key):
        raise NotImplementedError

    def decode(self, key):
        raise NotImplementedError

    def is_encoded(self, key):
        raise NotImplementedError

class VectorProvider(object):
    """Provider of unembedded vector (e.g., images, tweets). Applications
    must implement this class."""

    def __init__(self):
        self._vectors = []

    def get_vector(self, tasks):
        shuffled_tasks = tasks
        random.shuffle(shuffled_tasks)

        for task in shuffled_tasks:
            vector = self._find_vector(task)

            if vector is not None:
                del self._vectors[self._vectors.index(vector)]
                return (vector, task)

        return None

    def repurpose_vector(self, vector):
        self._vectors.append(vector)

    def _find_vector(self, task):
        raise NotImplementedError
