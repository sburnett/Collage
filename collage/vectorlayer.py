"""Vectors used to store messages; providers of those vectors.

You will probably need to override both of these classes
for your applications.

"""

import random

class Vector(object):
    """An abstract class for an immutable vector; encode and decode should
    create and return new copies of the vector, not mutate the data in the
    current vector."""

    def __init__(self, data, properties={}):
        """Initialize a vector with some properties.

        Properties are used to decide the types of tasks suitable for a vector.
        For example, if a task searches for pictures of "blue flowers", then
        only vectors of blue flowers should be used. This could be enforced by
        tagging each vector with descriptive keywords of its subject. For
        example, properties could be {'keywords': ['blue', 'flowers']}.

        """

        self._data = str(data)
        self._properties = dict(properties)

    def get_data(self):
        """Return the vector itself, e.g., a JPEG."""
        return self._data

    def get_property(self, key):
        return self._properties[key]

    def encode(self, data, key):
        """Store data inside this vector using information hiding.

        For keyed hiding schemes, the key will be required to decode the data.

        """
        raise NotImplementedError

    def estimate_max_capacity(self):
        """Estimate how much data can be stored inside this message."""
        raise NotImplementedError

    def decode(self, key):
        """Return the data stored in the vector, e.g., message chunks.
        
        For keyed hiding schemes, the key will be required to decode the data.

        """
        raise NotImplementedError

    def is_encoded(self, key):
        """Does this vector contain a hidden message?
        
        For keyed hiding schemes, an incorrect key will give wrong answers to
        this question.
        
        """
        raise NotImplementedError

class EncodingError(Exception):
    """This error is raised when some data cannot be encoded into a vector.
    
    The most common reason for this error is that information hiding algorithm,
    e.g., steganography or watermarking, cannot fit the data in the space
    available.
    
    """
    pass

class VectorProvider(object):
    """Provider of unembedded vectors (e.g., images, tweets). Applications
    must implement this class. Each task specifies constraints on the types
    of vectors that can be used with that task."""

    def __init__(self):
        """In your subclass, you should populate _vectors."""
        self._vectors = []

    def get_vector(self, tasks):
        """Given a list of tasks, find a vector for one of the tasks.
        
        Vectors are not reused, so they are removed from the pool
        once returned by this method.

        """
        
        shuffled_tasks = tasks
        random.shuffle(shuffled_tasks)

        for task in shuffled_tasks:
            vector = self._find_vector(task)

            if vector is not None:
                del self._vectors[self._vectors.index(vector)]
                return (vector, task)

        return None

    def repurpose_vector(self, vector):
        """Return a vector to the pool of possible vectors.

        This is called when a vector returned by get_vector is deemed unsuitable.
        For example, if get_vector returned a vector that was too small
        to hold a particular message, then that vector may be repurposed
        and reused later with a smaller message.

        """
        self._vectors.append(vector)

    def _find_vector(self, task):
        """Find a vector for a particular task.

        You must implement this method in your own vector providers. It
        will probably check properties of vectors to see if they can
        be used with this task.

        """
        raise NotImplementedError
