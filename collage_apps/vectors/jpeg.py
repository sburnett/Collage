"""Encode Collage messages inside JPEGs using OutGuess."""

import subprocess
import tempfile
import base64
import time
import os
import logging

import numpy
import hashlib

from collage.vectorlayer import Vector, EncodingError

class OutguessVector(Vector):
    def __init__(self, data, timeout=10, estimate_db=None, logger=None):
        super(OutguessVector, self).__init__(data)
        self._timeout = timeout
        self._decoded_data = None
        self._estimate_db = estimate_db
        if logger is None:
            self._logger = logging.getLogger('dummy')
        else:
            self._logger = logger

    def encode(self, message, key):
        self._logger.info('Encoding message "%s"', base64.b64encode(key))

        self._logger.info('Encoder writing data file')
        data_file = tempfile.NamedTemporaryFile()
        data_file.write(message)
        data_file.flush()

        self._logger.info('Encoder writing message file')
        cover_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        cover_file.write(self._data)
        cover_file.flush()

        dest_file = tempfile.NamedTemporaryFile(suffix='.jpg')

        self._logger.info('Encoder executing Outguess')
        command = ['outguess', '-k', base64.b64encode(key),
                   '-d', data_file.name,
                   cover_file.name, dest_file.name]
        proc = subprocess.Popen(command, stdout=open(os.devnull, 'w'),
                                         stderr=subprocess.STDOUT)

        time_left = self._timeout
        poll_interval = 1
        while time_left > 0 and proc.poll() is None:
            time.sleep(poll_interval)
            time_left -= poll_interval

        if proc.returncode is None or proc.returncode != 0:
            self._logger.error('Outguess returned error %s', str(proc.returncode))
            if proc.returncode is None:
                proc.terminate()
            raise EncodingError

        encoded = dest_file.read()
        encoded_vector = OutguessVector(encoded)

        if encoded_vector.decode(key) != message:
            self._logger.error('Encoding reversal test failed')
            raise EncodingError

        hash = hashlib.md5(encoded_vector.get_data()).hexdigest()
        self._logger.error('Encoded vector data, has MD5 hash %s', hash)
        print 'RETURNING: %s' % hash

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
        self._logger.info('Decoding message "%s" from image "%s"',
                          base64.b64encode(key),
                          hashlib.md5(self._data).hexdigest())
        if self._decoded_data is None:
            embedded_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            embedded_file.write(self._data)
            embedded_file.close()
            data_file = tempfile.NamedTemporaryFile()

            print '!DC image: ' + hashlib.md5(open(embedded_file.name, 'r').read()).hexdigest()
            print '!DC length: ' + str(len(open(embedded_file.name, 'r').read()))

            self._logger.info('Executing Outguess to decode image')
            command = ['outguess', '-k', base64.b64encode(key),
                       '-r', embedded_file.name,
                       data_file.name]
            self._logger.info('Outguess command is: %s', str(command))
            try:
                proc = subprocess.Popen(command)
            except OSError as exp:
                self._logger.info('Error executing Outguess: %s', exp.strerror)
                raise exp

            stdout, stderr = proc.communicate()

            self._logger.info('Outguess exited with code %d', proc.returncode)
            self._logger.info('Outguess stdout: %s', stdout)
            self._logger.info('Outguess stderr: %s', stderr)

            try:
                os.unlink(embedded_file.name)
            except OSError as exp:
                self._logger.info('Error removing temporary file: %s', exp.strerror)

            if proc.returncode != 0:
                return None

            self._decoded_data = data_file.read()
            self._logger.info('Decoded data of length %d with MD5 hash: "%s"',
                              len(self._decoded_data),
                              hashlib.md5(self._decoded_data).hexdigest())

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

