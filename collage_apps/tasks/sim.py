"""A simluated task, for performance evaluation.

Don't use this.

"""

import random
import os
import os.path
import time
import sys

from collage.messagelayer import Task

from vectors import SimulatedVector

class SimulatedTask(Task):
    def __init__(self, traffic_overhead,
                 time_overhead, time_deviation,
                 download, upload,
                 vectors_per_task,
                 storage_dir):
        self._traffic_overhead = traffic_overhead
        self._time_overhead = time_overhead
        self._time_deviation = time_deviation
        self._download = (download*1000)/8.
        self._upload = (upload*1000)/8.
        self._vectors_per_task = vectors_per_task
        self._storage_dir = storage_dir

    def send(self, id, vector):
        for i in range(self._vectors_per_task):
            filename = os.path.join(self._storage_dir, str(random.getrandbits(32)) + '.vector')
            open(filename, 'w').write(vector.get_data())
            traffic = len(vector.get_data()) + self._traffic_overhead
            tottime = traffic/self._upload + random.gauss(self._time_overhead, self._time_deviation)
            sys.stderr.write('%f %s\n' % (time.time(), 'send traffic %d time %d' % (traffic, tottime)))

    def receive(self, id):
        msgs = []
        for i in range(self._vectors_per_task):
            files = filter(lambda f: os.path.splitext(f)[1] == '.vector', os.listdir(self._storage_dir))
            filename = random.choice(files)
            data = open(os.path.join(self._storage_dir, filename), 'r').read()
            traffic = len(data) + self._traffic_overhead
            tottime = traffic/self._download + random.gauss(self._time_overhead, self._time_deviation)
            sys.stderr.write('%f %s\n' % (time.time(), 'receive traffic %d time %d' % (traffic, tottime)))
            yield SimulatedVector(data, 0.0)

    def can_embed(self, id, data):
        return True
