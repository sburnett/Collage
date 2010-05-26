import random
import time

from collage.vectorlayer import VectorProvider

from collage_apps.vectors.jpeg import DonatedOutguessVector

class DonatedVectorProvider(VectorProvider):
    def __init__(self, database, killswitch, estimate_db=None):
        super(DonatedVectorProvider, self).__init__()

        self._db = database
        self._killswitch = killswitch
        self._estimate_db = estimate_db

    def get_vector(self, tasks):
        shuffled_tasks = tasks
        random.shuffle(shuffled_tasks)

        while not self._killswitch.is_set():
            for task in shuffled_tasks:
                vector = self._find_vector(task)

                if vector is not None:
                    return (vector, task)

            time.sleep(1)

        return None

    def _find_vector(self, task):
        if self._killswitch.is_set():
            return None

        attrs = task.get_attributes()
        vectors = self._db.find_vectors(attrs)

        if len(vectors) > 0:
            key = vectors[0]
            data = open(self._db.get_filename(key), 'rb').read()
            return DonatedOutguessVector(data, key, estimate_db=self._estimate_db)
        else:
            return None
