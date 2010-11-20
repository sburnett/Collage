"""A database of donated vectors.

This database tracks the status of vectors donated by community volunteers. 
The following entities read and write to this database:
* The donation clients. This is an application that receives donations from users.
  For example, we provide both a Web application and desktop application that
  Flickr users can use to donate their photos. These clients access the database
  via RPC. (See urls.py)
* The application backend. After the donation clients provide raw, unembedded
  vectors the applications find these vectors and encode them with data. After,
  these vectors get sent back to the clients. (Or, more accurately, the clients
  poll for completed vectors.)
* The garbage collector. Vectors that have been in the database too long are
  expired and sent back to the clients unmodified. Eventually they are purged
  from the database to conserve space.

"""

import sqlite3
import os.path
import os
import sys
import random
import time
import datetime

import pdb

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

        cur = self._conn.execute('''SELECT name FROM applications WHERE name = ?''', (application,))
        if cur.fetchone() is None:
            return 'Invalid application name: %s' % application

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

    def update_attributes(self, key, value, new_key, new_value):
        cur = self._conn.execute('''SELECT vector_id FROM metadata
                                    WHERE key = ? AND value = ?''',
                                    (key, value))
        for row in cur:
            self._conn.execute('''DELETE FROM metadata
                                  WHERE vector_id = ?
                                  AND key = ?''',
                               (row['vector_id'], new_key))
            self._conn.execute('''INSERT INTO metadata
                                  (vector_id, key, value)
                                  VALUES (?, ?, ?)''',
                               (row['vector_id'], new_key, new_value))
        self._conn.commit()

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

class UploaderDatabase(DonationDatabase):
    def __init__(self, db_dir):
        super(UploaderDatabase, self).__init__(db_dir)

    def collect(self, attributes):
        """Return a list of vectors that are ready for to be
        uploaded, and are compatible with all of a set of attributes."""
        
        cur = self._conn.execute('''SELECT rowid FROM vectors
                                    WHERE done = 1''')
        vec_sec = set()
        for row in cur:
            vec_sec.add(row['rowid'])

        vector_ids = [vec_sec]

        for (key, value) in attributes:
            vec_set = set()
            cur = self._conn.execute('''SELECT vector_id FROM metadata,vectors
                                        WHERE metadata.key = ?
                                        AND value = ?
                                        AND done = 1''',
                                    (key, value))
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

    def get_attributes(self, key):
        attrs = []

        cur = self._conn.execute('''SELECT metadata.key,value
                                    FROM metadata,vectors
                                    WHERE vector_id = vectors.rowid
                                    AND vectors.key = ?''',
                                 (key,))
        for row in cur:
            attrs.append((row['key'], row['value']))

        return attrs

    def delete(self, key):
        """Erase vector matching a key."""

        row = self._conn.execute('''SELECT rowid FROM vectors
                                    WHERE key = ?''', (key,)).fetchone()
        if row is None:
            return

        self._conn.execute('''DELETE FROM metadata
                              WHERE vector_id = ?''', (row['rowid'],))
        self._conn.execute('''DELETE FROM vectors
                              WHERE rowid = ?''', (row['rowid'],))
        try:
            os.unlink(self.get_filename(key))
        except OSError:
            pass

        self._conn.commit()

class AppDatabase(DonationDatabase):
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
        
        cur = self._conn.execute('''SELECT rowid FROM vectors
                                    WHERE done = 0''')
        vec_sec = set()
        for row in cur:
            vec_sec.add(row['rowid'])

        vector_ids = [vec_sec]

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

class CleanupDatabase(DonationDatabase):
    def __init__(self, db_dir):
        super(CleanupDatabase, self).__init__(db_dir)

    def cleanup(self):
        """Mark vectors that are older than their expiration date
        as "done", so that they can be returned to their owners
        to be uploaded without embedded content."""

        cur = self._conn.execute('''SELECT rowid,key FROM vectors
                                    WHERE strftime('%s', expiration)
                                          < strftime('%s', current_timestamp)''')

        for row in cur:
            self._conn.execute('''UPDATE vectors SET done = 1
                                  WHERE rowid = ?''', (row['rowid'],))

            #self._conn.execute('''DELETE FROM metadata
            #                      WHERE vector_id = ?''', (row['rowid'],))
            #self._conn.execute('''DELETE FROM vectors
            #                      WHERE rowid = ?''', (row['rowid'],))
            #try:
            #    os.unlink(self.get_filename(row['key']))
            #except OSError:
            #    pass

        self._conn.commit()
