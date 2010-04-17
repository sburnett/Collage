import sqlite3
import os.path
import os
import sys
import random
import time
import datetime

default_dir = 'vectors'
db_name = 'donation.sqlite'

class DonationDatabase(object):
    _max_expiration = datetime.timedelta(7,) # 1 week

    def __init__(self, db_dir):
        """The database directory should dedicated to the donation
        server, as other files may get overwritten."""

        if not os.path.isdir(db_dir):
            raise OSError('"%s" is not a directory' % db_dir)

        self._conn = sqlite3.connect(os.path.join(db_dir, db_name))
        self._conn.row_factory = sqlite3.Row

        self._conn.execute('''CREATE TABLE IF NOT EXISTS applications
                              (name TEXT PRIMARY KEY)''')
        self._conn.execute('''CREATE TABLE IF NOT EXISTS vectors
                              (application REFERENCES applications (name),
                               expiration TEXT,
                               key TEXT,
                               done INTEGER(1))''')
        self._conn.execute('''CREATE TABLE IF NOT EXISTS metadata
                              (vector_id REFERENCES vectors (rowid),
                               key TEXT,
                               value TEXT)''')

        self._vector_dir = db_dir

        self._conn.commit()

    def get_filename(self, key):
        """For a given key, return the name of the file
        that contains the vector data for that key."""

        return os.path.join(self._vector_dir, '%s' % (key,))

class DonaterDatabase(DonationDatabase):
    def __init__(self, db_dir):
        super(DonaterDatabase, self).__init__(db_dir)

    def donate(self, data, application, attributes, expiration=datetime.timedelta(1,)):
        """Add a new vector for donation to a particular application.
           The vector is kept around until an expiration is reached,
           then it is deleted from disk. The caller is given back a
           random key, which must be given to collect the vector."""

        secretkey = '%.16x' % random.randint(0, sys.maxint)
        expiration = min(expiration, self._max_expiration)
        expire_time = (datetime.datetime.utcnow() + expiration).isoformat()

        open(self.get_filename(secretkey), 'w').write(data)

        cur = self._conn.execute('''INSERT INTO vectors
                                    (application, expiration, key, done)
                                    VALUES (?, ?, ?, ?)''',
                                (application, expire_time, secretkey, 0))
        rowid = cur.lastrowid

        for (key, value) in attributes:
            self._conn.execute('''INSERT INTO metadata
                                  (vector_id, key, value)
                                  VALUES (?, ?, ?)''',
                              (rowid, key, value))
        
        self._conn.commit()

        return secretkey

    def collect(self, key):
        """Retrieve a vector, iff it has been embedded with data."""

        cur = self._conn.execute('''SELECT rowid FROM vectors
                                    WHERE key = ?
                                    AND done = 1''',
                                 (key,))
        row = cur.fetchone()
        if row is not None:
            return open(self.get_filename(key), 'r').read()
        else:
            return None

def AppDatabase(DonationDatabase):
    def __init__(self, db_dir, application):
        super(AppDatabase, self).__init__(db_dir)

        self._application = application
        self.register_application(application)

    def register_application(self, name):
        """Add a new application name if it doesn't already exist."""

        self._conn.execute('INSERT OR IGNORE INTO applications (name) VALUES (?)', (name,))
        self._conn.commit()

    def unregister_application(self, name):
        """Delete an application name."""

        self._conn.execute('DELETE FROM applications WHERE name = ?', (name,))
        self._conn.commit()

    def find_vectors(self, attributes):
        """Return a list of vectors that are ready for to be
        encoded, and are compatible with all of a set of attributes."""
        
        vector_ids = []

        for (key, value) in attributes:
            vec_set = set()
            cur = self._conn.execute('''SELECT vector_id FROM metadata,vectors
                                        WHERE metadata.key = ?
                                        AND value = ?
                                        AND done = 0
                                        AND application = ?''',
                                    (key, value, self._application))
            for row in cur:
                vec_set.add(row['vector_id'])

            vector_ids.append(vec_set)

        keys = []
        for rowid in reduce(lambda a, b: a & b, vector_ids):
            cur = self._conn.execute("""SELECT key FROM vectors
                                        WHERE rowid = ?""",
                                     (rowid,))
            row = cur.fetchone()

            if row is not None:
                keys.append(row['key'])

        return keys

    def mark_done(self, key):
        """Notify the database that a given vector is ready has
        been encoded with data and is thus ready for collection."""

        self._conn.execute('''UPDATE vectors
                              SET done = 1
                              WHERE key = ?''',
                           (key,))
        self._conn.commit()

    def cleanup(self):
        """Erase vectors that are older than their expiration data."""

        cur = self._conn.execute('''SELECT rowid,key FROM vectors
                                    WHERE expiration < CURRENT_TIMESTAMP''')

        for row in cur:
            self._conn.execute('''DELETE FROM metadata
                                  WHERE vector_id = ?''', (row['rowid'],))
            self._conn.execute('''DELETE FROM vectors
                                  WHERE rowid = ?''', (row['rowid'],))
            try:
                os.unlink(self.get_filename(row['key']))
            except OSError:
                pass

        self._conn.commit()
