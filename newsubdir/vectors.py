import subprocess
import tempfile
import base64
import time

from collage.vectorlayer import Vector, EncodingError

class OutguessVector(Vector):
    def __init__(self, data, timeout=10):
        super(OutguessVector, self).__init__(data)
        self._timeout = timeout
        self._decoded_data = None

    def encode(self, data, key):
        data_file = tempfile.NamedTemporaryFile()
        data_file.write(data)
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
        return OutguessVector(encoded)

    def decode(self, key):
        if self._decoded_data is None:
            embedded_file = tempfile.NamedTemporaryFile(suffix='.jpg')
            embedded_file.write(self._data)
            embedded_file.flush()
            data_file = tempfile.NamedTemporaryFile()

            command = ['outguess', '-k', base64.b64encode(key),
                       '-r', embedded_file.name,
                       data_file.name]
            retcode = subprocess.call(command, stdout=open('/dev/null', 'w'),
                                               stderr=subprocess.STDOUT)

            if retcode != 0:
                return None

            self._decoded_data = data_file.read()

        return self._decoded_data

    def is_encoded(self, key):
        return self.decode(key) is not None

    def __cmp__(self, other):
        return cmp(self._data, other._data)
