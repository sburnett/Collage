import random

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
                del self._vectors.index(vector)
                return vector

        return None

    def repurpose_vector(self, vector):
        self._vectors.append(vector)

    def _find_vector(self, task):
        raise NotImplementedError
