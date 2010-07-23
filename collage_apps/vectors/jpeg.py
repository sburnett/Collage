import subprocess
import tempfile
import base64
import time

import numpy
import hashlib

from collage.vectorlayer import Vector, EncodingError

class OutguessVector(Vector):
    def __init__(self, data, timeout=10, estimate_db=None):
        super(OutguessVector, self).__init__(data)
        self._timeout = timeout
        self._decoded_data = None
        self._estimate_db = estimate_db

    def encode(self, message, key):
        data_file = tempfile.NamedTemporaryFile()
        data_file.write(message)
        data_file.flush()

        cover_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        cover_file.write(self._data)
        cover_file.flush()

        dest_file = tempfile.NamedTemporaryFile(suffix='.jpg')

        command = ['outguess', '-k', base64.b64encode(key), 
                   '-d', data_file.name,
                   cover_file.name, dest_file.name]
        proc = subprocess.Popen(command, stdout=open('/dev/null', 'w'),
                                         stderr=subprocess.STDOUT)

        time_left = self._timeout
        poll_interval = 1
        while time_left > 0 and proc.poll() is None:
            time.sleep(poll_interval)
            time_left -= poll_interval

        if proc.returncode is None or proc.returncode != 0:
            if proc.returncode is None:
                proc.terminate()
            raise EncodingError

        encoded = dest_file.read()
        encoded_vector = OutguessVector(encoded)

        if encoded_vector.decode(key) != message:
            raise EncodingError

        print 'RETURNING: %s' % hashlib.md5(encoded_vector.get_data()).hexdigest()
        return encoded_vector

    def estimate_max_capacity(self):
        if self._estimate_db is None:
            return 2
        
        class_name = self.__class__.__name__
        if class_name not in self._estimate_db:
            return 2

        xp = []
        yp = []
        for size in sorted(self._estimate_db[class_name].keys()):
            for capacity in self._estimate_db[class_name][size]:
                xp.append(size)
                yp.append(capacity)

        try:
            interped = int(numpy.interp(len(self._data), xp, yp))
        except:
            interped = 2
        return max(interped, 2)

    def record_estimate(self, estimate):
        if self._estimate_db is not None:
            mylen = len(self._data)
            class_name = self.__class__.__name__
            self._estimate_db.setdefault(class_name, {})
            self._estimate_db[class_name].setdefault(mylen, [])
            self._estimate_db[class_name][mylen].append(estimate)
            self._estimate_db.sync()

    def decode(self, key):
        print 'Key: %s' % base64.b64encode(key)
        print 'Image hash: %s' % hashlib.md5(self._data).hexdigest()
        if self._decoded_data is None:
            embedded_file = tempfile.NamedTemporaryFile(suffix='.jpg')
            embedded_file.write(self._data)
            embedded_file.flush()
            data_file = tempfile.NamedTemporaryFile()

            print '!DC image: ' + hashlib.md5(open(embedded_file.name, 'r').read()).hexdigest()
            print '!DC length: ' + str(len(open(embedded_file.name, 'r').read()))

            command = ['outguess', '-k', base64.b64encode(key),
                       '-r', embedded_file.name,
                       data_file.name]
            print '!DC command: ' + str(command)
            retcode = subprocess.call(command, stdout=open('/dev/null', 'w'),
                                               stderr=subprocess.STDOUT)

            if retcode != 0:
                return None

            self._decoded_data = data_file.read()
            print '!DC data: %s' % hashlib.md5(self._decoded_data).hexdigest()

        return self._decoded_data

    def is_encoded(self, key):
        return self.decode(key) is not None

    def __cmp__(self, other):
        return cmp(self._data, other._data)

class DonatedOutguessVector(OutguessVector):
    def __init__(self, data, key, estimate_db=None):
        super(DonatedOutguessVector, self).__init__(data, estimate_db=estimate_db)
        self._key = key

    def encode(self, data, key):
        vec = super(DonatedOutguessVector, self).encode(data, key)
        return DonatedOutguessVector(vec.get_data(), self._key)

    def get_key(self):
        return self._key

