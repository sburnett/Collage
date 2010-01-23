import sqlite3
import hashlib
import os.path
import sys
import random
import time
import datetime
from Crypto.Cipher import AES
import struct
import math

default_database = 'donation.sqlite'
default_dir = 'vectors'

class DonationDatabase(object):
    _max_expiration = datetime.timedelta(7,) # 1 week
    _done_string = 'done'

    def __init__(self, database=default_database, application=None, vector_dir=default_dir):
        self._conn = sqlite3.connect(database)
        self._conn.row_factory = sqlite3.Row

        self._conn.execute('''CREATE TABLE IF NOT EXISTS applications
                             (name TEXT PRIMARY KEY)''')
        self._conn.execute('''CREATE TABLE IF NOT EXISTS vectors
                             (application REFERENCES applications (name),
                              expiration TEXT,
                              key TEXT,
                              status TEXT)''')
        self._conn.execute('''CREATE TABLE IF NOT EXISTS metadata
                             (vector_id REFERENCES vectors (rowid),
                              key TEXT,
                              value TEXT)''')

        self._application = application
        self._conn.execute('''INSERT OR IGNORE INTO applications (name)
                              VALUES (?)''', (self._application,))
        self._vector_dir = vector_dir

        self._conn.commit()

    def register_application(self, name):
        self._conn.execute('INSERT OR IGNORE INTO applications (name) VALUES (?)', (name,))
        self._conn.commit()

    def unregister_application(self, name):
        self._conn.execute('DELETE FROM applications WHERE name = ?', (name,))
        self._conn.commit()

    def get_filename(self, key):
        return os.path.join(self._vector_dir, '%s' % (key,))

    def donate(self, data, application, attributes, expiration=datetime.timedelta(1,)):
        salt = str(random.randint(0, 65535))
        secretkey = hashlib.sha1(salt + data).hexdigest()[24:]
        expiration = min(expiration, self._max_expiration)
        expire_time = (datetime.datetime.utcnow() + expiration).isoformat()

        open(self.get_filename(secretkey), 'w').write(data)

        cur = self._conn.execute('''INSERT INTO vectors
                                   (application, expiration, key, status)
                                   VALUES (?, ?, ?, ?)''',
                                (application, expire_time, secretkey, ''))
        rowid = cur.lastrowid

        for (key, value) in attributes:
            self._conn.execute('''INSERT INTO metadata
                                 (vector_id, key, value)
                                 VALUES (?, ?, ?)''',
                              (rowid, key, value))
        
        self._conn.commit()

        return secretkey

    def _prepare_data(self, key):
            data = open(self.get_filename(key), 'r').read()
            encrypter = AES.new(key)
            datalen = (len(data)/AES.block_size)*AES.block_size - 1
            while datalen < len(data):
                datalen += AES.block_size
            payload = struct.pack('B%ds' % datalen, datalen - len(data), data)
            ciphertext = encrypter.encrypt(payload)
            open('/tmp/test', 'w').write(ciphertext)
            return ciphertext

    def collect(self, key):
        cur = self._conn.execute("""SELECT rowid FROM vectors
                                    WHERE key = ?
                                    AND status = ?""",
                                 (key, self._done_string))
        row = cur.fetchone()
        if row is not None:
            return self._prepare_data(key)
        else:
            return None

    def find_vectors(self, attributes):
        if self._application is None:
            raise AttributeError

        vector_ids = []

        for (key, value) in attributes:
            vec_set = set()
            cur = self._conn.execute("""SELECT vector_id FROM metadata,vectors
                                       WHERE metadata.key = ?
                                       AND value = ?
                                       AND application = ?""",
                                    (key, value, self._application))
            for row in cur:
                vec_set.add(row['vector_id'])

            vector_ids.append(vec_set)

        keys = []
        for rowid in reduce(lambda a, b: a & b, vector_ids):
            cur = self._conn.execute("""SELECT key FROM vectors
                                        WHERE rowid = ? AND status = ''""",
                                    (rowid,))
            row = cur.fetchone()

            if row is not None:
                keys.append(row['key'])

        return keys

    def mark_done(self, key):
        self._conn.execute('''UPDATE vectors
                             SET status = ?
                             WHERE key = ?''',
                           (self._done_string, key))
        self._conn.commit()

    def cleanup(self):
        cur = self._conn.execute('''SELECT rowid FROM vectors
                                    WHERE expiration < CURRENT_TIMESTAMP''')

        for row in cur:
            self._conn.execute('''DELETE FROM metadata
                                  WHERE vector_id = ?''', (row['rowid'],))
            self._conn.execute('''DELETE FROM vectors
                                  WHERE rowid = ?''', (row['rowid'],))

        self._conn.commit()
